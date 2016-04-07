import click
from didata_cli.cli import pass_client
from didata_cli.filterable_response import DiDataCLIFilterableResponse
from libcloud.common.dimensiondata import DimensionDataAPIException
from didata_cli.utils import handle_dd_api_exception, get_single_server_id_from_filters
from collections import OrderedDict


@click.group()
@pass_client
def cli(client):
    pass


@cli.command()
@click.option('--serverId', required=True, help="The server ID to get info for")
@click.option('--query', help="The query to pass to the printer")
@pass_client
def info(client, serverid, query):
    node = client.node.ex_get_node_by_id(serverid)
    if node:
        response = DiDataCLIFilterableResponse()
        response.add(_node_to_dict(node))
        if query is not None:
            response.do_filter(query)
        click.secho(response.to_string(client.output_type))
    else:
        click.secho("No node found for id {0}".format(serverid), fg='red', bold=True)


@cli.command()
@click.option('--datacenterId', type=click.UNPROCESSED, help="Filter by datacenter Id")
@click.option('--networkDomainId', type=click.UNPROCESSED, help="Filter by network domain Id")
@click.option('--networkId', type=click.UNPROCESSED, help="Filter by network id")
@click.option('--vlanId', type=click.UNPROCESSED, help="Filter by vlan id")
@click.option('--sourceImageId', type=click.UNPROCESSED, help="Filter by source image id")
@click.option('--deployed', help="Filter by deployed state")
@click.option('--name', help="Filter by server name")
@click.option('--state', help="Filter by state")
@click.option('--started', help="Filter by started")
@click.option('--ipv6', help="Filter by ipv6")
@click.option('--privateIpv4', help="Filter by private ipv4")
@click.option('--idsonly', is_flag=True, default=False, help="Only dump server ids")
@click.option('--query', help="The query to pass to the printer")
@pass_client
def list(client, datacenterid, networkdomainid, networkid,
         vlanid, sourceimageid, deployed, name,
         state, started, ipv6, privateipv4, idsonly, query):
    node_list = client.node.list_nodes(ex_location=datacenterid, ex_name=name, ex_network=networkid,
                                       ex_network_domain=networkdomainid, ex_vlan=vlanid,
                                       ex_image=sourceimageid, ex_deployed=deployed, ex_started=started,
                                       ex_state=state, ex_ipv6=ipv6, ex_ipv4=privateipv4)
    response = DiDataCLIFilterableResponse()
    for node in node_list:
        if idsonly:
            click.secho(node.id)
        else:
            response.add(_node_to_dict(node))
    if not response.is_empty():
        if query is not None:
            response.do_filter(query)
        click.secho(response.to_string(client.output_type))
    else:
        click.secho("No nodes found", fg='red', bold=True)


@cli.command()
@click.option('--name', required=True, help="The name of the server")
@click.option('--description', required=True, help="The description of the server")
@click.option('--imageId', required=True, type=click.UNPROCESSED, help="The image id for the server")
@click.option('--autostart', is_flag=True, default=False, help="Bool flag for if you want to autostart")
@click.option('--administratorPassword', required=True, type=click.UNPROCESSED, help="The administrator password")
@click.option('--networkDomainId', required=True, type=click.UNPROCESSED, help="The network domain Id to deploy on")
@click.option('--vlanId', required=True, type=click.UNPROCESSED, help="The vlan Id to deploy on")
@pass_client
def create(client, name, description, imageid, autostart, administratorpassword, networkdomainid, vlanid):
    try:
        response = client.node.create_node(name, imageid, administratorpassword,
                                           description, ex_network_domain=networkdomainid,
                                           ex_vlan=vlanid, ex_is_started=autostart)
        click.secho("Node starting up: {0}.  IPv6: {1}".format(response.id, response.extra['ipv6']),
                    fg='green', bold=True)
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)


@cli.command()
@click.option('--serverId', type=click.UNPROCESSED, help='The server ID to destroy')
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@click.option('--ramInGB', required=True, help='Amount of RAM to change the server to', type=int)
@pass_client
def update_ram(client, serverid, serverfilteripv6, ramingb):
    node = None
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ex_ipv6=serverfilteripv6)
    node = client.node.ex_get_node_by_id(serverid)
    try:
        client.node.ex_reconfigure_node(node, ramingb, None, None, None)
        click.secho("Server {0} ram is being changed to {1}GB".format(serverid, ramingb), fg='green', bold=True)
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)


@cli.command()
@click.option('--serverId', type=click.UNPROCESSED, help='The server ID to destroy')
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@click.option('--cpuCount', required=True, help='# of CPUs to change to', type=int)
@pass_client
def update_cpu_count(client, serverid, serverfilteripv6, cpucount):
    node = None
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ex_ipv6=serverfilteripv6)
    node = client.node.ex_get_node_by_id(serverid)
    try:
        client.node.ex_reconfigure_node(node, None, cpucount, None, None)
        click.secho("Server {0} CPU Count changing to {1}".format(serverid, cpucount), fg='green', bold=True)
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)


@cli.command()
@click.option('--serverId', type=click.UNPROCESSED, help='The server ID to destroy')
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@pass_client
def destroy(client, serverid, serverfilteripv6):
    node = None
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ex_ipv6=serverfilteripv6)
    node = client.node.ex_get_node_by_id(serverid)
    try:
        response = client.node.destroy_node(node)
        if response is True:
            click.secho("Server {0} is being destroyed".format(serverid), fg='green', bold=True)
        else:
            click.secho("Something went wrong with attempting to destroy {0}".format(serverid))
            exit(1)
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)


@cli.command()
@click.option('--serverId', type=click.UNPROCESSED, help='The server ID to reboot')
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@pass_client
def reboot(client, serverid, serverfilteripv6):
    node = None
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ex_ipv6=serverfilteripv6)
    node = client.node.ex_get_node_by_id(serverid)
    try:
        response = client.node.reboot_node(node)
        if response is True:
            click.secho("Server {0} is being rebooted".format(serverid), fg='green', bold=True)
        else:
            click.secho("Something went wrong with attempting to reboot {0}".format(serverid))
            exit(1)
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)


@cli.command()
@click.option('--serverId', type=click.UNPROCESSED, help='The server ID to reboot')
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@pass_client
def reboot_hard(client, serverid, serverfilteripv6):
    node = None
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ex_ipv6=serverfilteripv6)
    node = client.node.ex_get_node_by_id(serverid)
    try:
        response = client.node.ex_reset(node)
        if response is True:
            click.secho("Server {0} is being rebooted".format(serverid), fg='green', bold=True)
        else:
            click.secho("Something went wrong with attempting to reboot {0}".format(serverid))
            exit(1)
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)


@cli.command()
@click.option('--serverId', type=click.UNPROCESSED, help='The server ID to start')
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@pass_client
def start(client, serverid, serverfilteripv6):
    node = None
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ex_ipv6=serverfilteripv6)
    node = client.node.ex_get_node_by_id(serverid)
    try:
        response = client.node.ex_start_node(node)
        if response is True:
            click.secho("Server {0} is starting".format(serverid), fg='green', bold=True)
        else:
            click.secho("Something went wrong when attempting to start {0}".format(serverid))
            exit(1)
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)


@cli.command()
@click.option('--serverId', type=click.UNPROCESSED, help='The server ID to shutdown')
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@pass_client
def shutdown(client, serverid, serverfilteripv6):
    node = None
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ex_ipv6=serverfilteripv6)
    node = client.node.ex_get_node_by_id(serverid)
    try:
        response = client.node.ex_shutdown_graceful(node)
        if response is True:
            click.secho("Server {0} is shutting down gracefully".format(serverid), fg='green', bold=True)
        else:
            click.secho("Something went wrong when attempting to shutdown {0}".format(serverid))
            exit(1)
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)


@cli.command()
@click.option('--serverId', type=click.UNPROCESSED, help='The server ID to shutdown')
@click.option('--serverFilterIpv6', help='The filter for ipv6')
@pass_client
def shutdown_hard(client, serverid, serverfilteripv6):
    node = None
    if not serverid:
        serverid = get_single_server_id_from_filters(client, ex_ipv6=serverfilteripv6)
    node = client.node.ex_get_node_by_id(serverid)
    try:
        response = client.node.ex_power_off(node)
        if response is True:
            click.secho("Server {0} is shutting down hard".format(serverid), fg='green', bold=True)
        else:
            click.secho("Something went wrong when attempting to shutdown {0}".format(serverid))
            exit(1)
    except DimensionDataAPIException as e:
        handle_dd_api_exception(e)


def _node_to_dict(node):
    node_dict = OrderedDict()
    node_dict['Name'] = node.name
    node_dict['ID'] = node.id
    ip_count = 0
    for ip in node.private_ips:
        node_dict['Private IPv4 ' + str(ip_count)] = ip
    node_dict['State'] = node.state
    for key in sorted(node.extra):
        if key == 'cpu':
            node_dict['CPU Count'] = node.extra[key].cpu_count
            node_dict['Cores per Socket'] = node.extra[key].cores_per_socket
            node_dict['CPU Performance'] = node.extra[key].performance
            continue
        if key == 'disks':
            for disk in node.extra[key]:
                node_dict['Disk ' + str(disk.scsi_id) + ' ID'] = disk.id
                node_dict['Disk ' + str(disk.scsi_id) + ' Size'] = disk.size_gb
                node_dict['Disk ' + str(disk.scsi_id) + ' Speed'] = disk.speed
                node_dict['Disk ' + str(disk.scsi_id) + ' State'] = disk.state
            continue
        # skip this key, it is similar to node.status
        if key == 'status':
            continue
        node_dict[key] = node.extra[key]
    return node_dict
