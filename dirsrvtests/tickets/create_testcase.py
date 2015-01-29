import sys
import optparse

'''
    This script generates a template test script that handles the
    non-interesting parts of a test script:
        topology,
        test (to be completed by the user),
        final,
        and run-isolated functions
'''


def displayUsage():
    print ('\nUsage:\ncreate_ticket.py -t|--ticket <ticket number> [ i|--instances ' +
           '<number of standalone instances> [ -m|--masters <number of masters> ' +
           '-h|--hubs <number of hubs> -c|--consumers <number of consumers> ] ' +
           '-o|--outputfile ]\n')
    print ('If only "-t" is provided then a single standalone instance is created.  ' +
           'The "-i" option can add mulitple standalone instances(maximum 10).  ' +
           'However, you can not mix "-i" with the replication options(-m, -h , -c).  ' +
           'There is a maximum of 10 masters, 10 hubs, and 10 consumers.')
    exit(1)

desc = 'Script to generate an initial lib389 test script.  ' + \
       'This generates the topology, test, final, and run-isolated functions.'

if len(sys.argv) > 0:
    parser = optparse.OptionParser(description=desc, add_help_option=False)

    # Script options
    parser.add_option('-t', '--ticket', dest='ticket', default=None)
    parser.add_option('-i', '--instances', dest='inst', default=None)
    parser.add_option('-m', '--masters', dest='masters', default='0')
    parser.add_option('-h', '--hubs', dest='hubs', default='0')
    parser.add_option('-c', '--consumers', dest='consumers', default='0')
    parser.add_option('-o', '--outputfile', dest='filename', default=None)

    # Validate the options
    try:
        (args, opts) = parser.parse_args()
    except:
        displayUsage()

    if args.ticket is None:
        print 'Missing required ticket number'
        displayUsage()

    if int(args.masters) == 0:
        if int(args.hubs) > 0 or int(args.consumers) > 0:
            print 'You must use "-m|--masters" if you want to have hubs and/or consumers'
            displayUsage()

    if not args.masters.isdigit() or int(args.masters) > 10 or int(args.masters) < 0:
        print 'Invalid value for "--masters", it must be a number and it can not be greater than 10'
        displayUsage()

    if not args.hubs.isdigit() or int(args.hubs) > 10 or int(args.hubs) < 0:
        print 'Invalid value for "--hubs", it must be a number and it can not be greater than 10'
        displayUsage()

    if not args.consumers.isdigit() or int(args.consumers) > 10 or int(args.consumers) < 0:
        print 'Invalid value for "--consumers", it must be a number and it can not be greater than 10'
        displayUsage()

    if args.inst:
        if not args.inst.isdigit() or int(args.inst) > 10 or int(args.inst) < 1:
            print ('Invalid value for "--instances", it must be a number greater than 0 ' +
                   'and not greater than 10')
            displayUsage()
        if int(args.inst) > 0:
            if int(args.masters) > 0 or int(args.hubs) > 0 or int(args.consumers) > 0:
                print 'You can not mix "--instances" with replication.'
                displayUsage()

    # Extract usable values
    masters = int(args.masters)
    hubs = int(args.hubs)
    consumers = int(args.consumers)
    ticket = args.ticket
    if not args.inst:
        instances = 1
    else:
        instances = int(args.inst)
    filename = args.filename

    #
    # Create/open the new test script file
    #
    if not filename:
        filename = 'ticket' + ticket + '_test.py'
    try:
        TEST = open(filename, "w")
    except IOError:
        print "Can\'t open file:", filename
        exit(1)

    #
    # Write the imports
    #
    TEST.write('import os\nimport sys\nimport time\nimport ldap\nimport ldap.sasl\n' +
               'import logging\nimport socket\nimport pytest\n')
    TEST.write('from lib389 import DirSrv, Entry, tools, tasks\nfrom lib389.tools import DirSrvTools\n' +
               'from lib389._constants import *\nfrom lib389.properties import *\nfrom lib389.tasks import *\n\n')

    #
    # Set the logger and installation prefix
    #
    TEST.write('logging.getLogger(__name__).setLevel(logging.DEBUG)\n')
    TEST.write('log = logging.getLogger(__name__)\n\n')
    TEST.write('installation1_prefix = None\n\n\n')

    #
    # Write the replication or standalone classes
    #
    repl_deployment = False
    if masters + hubs + consumers > 0:
        #
        # Write the replication class
        #
        repl_deployment = True

        TEST.write('class TopologyReplication(object):\n')
        TEST.write('    def __init__(self')
        for idx in range(masters):
            TEST.write(', master' + str(idx + 1))
        for idx in range(hubs):
            TEST.write(', hub' + str(idx + 1))
        for idx in range(consumers):
            TEST.write(', consumer' + str(idx + 1))
        TEST.write('):\n')

        for idx in range(masters):
            TEST.write('        master' + str(idx + 1) + '.open()\n')
            TEST.write('        self.master' + str(idx + 1) + ' = master' + str(idx + 1) + '\n')
        for idx in range(hubs):
            TEST.write('        hub' + str(idx + 1) + '.open()\n')
            TEST.write('        self.hub' + str(idx + 1) + ' = hub' + str(idx + 1) + '\n')
        for idx in range(consumers):
            TEST.write('        consumer' + str(idx + 1) + '.open()\n')
            TEST.write('        self.consumer' + str(idx + 1) + ' = consumer' + str(idx + 1) + '\n')
        TEST.write('\n\n')
    else:
        #
        # Write the standalone class
        #
        TEST.write('class TopologyStandalone(object):\n')
        TEST.write('    def __init__(self')
        for idx in range(instances):
            idx += 1
            if idx == 1:
                idx = ''
            else:
                idx = str(idx)
            TEST.write(', standalone' + idx)
        TEST.write('):\n')

        for idx in range(instances):
            idx += 1
            if idx == 1:
                idx = ''
            else:
                idx = str(idx)
            TEST.write('        standalone' + idx + '.open()\n')
            TEST.write('        self.standalone' + idx + ' = standalone' + idx + '\n')
        TEST.write('\n\n')

    #
    # Write the 'topology function'
    #
    TEST.write('@pytest.fixture(scope="module")\n')
    TEST.write('def topology(request): \n')
    TEST.write('    global installation1_prefix\n')
    TEST.write('    if installation1_prefix:\n')
    TEST.write('        args_instance[SER_DEPLOYED_DIR] = installation1_prefix\n\n')

    if repl_deployment:
        #
        # Create the replication instances
        #
        for idx in range(masters):
            idx = str(idx + 1)
            TEST.write('    # Creating master ' + idx + '...\n')
            TEST.write('    master' + idx + ' = DirSrv(verbose=False)\n')
            TEST.write('    args_instance[SER_HOST] = HOST_MASTER_' + idx + '\n')
            TEST.write('    args_instance[SER_PORT] = PORT_MASTER_' + idx + '\n')
            TEST.write('    args_instance[SER_SERVERID_PROP] = SERVERID_MASTER_' + idx + '\n')
            TEST.write('    args_master = args_instance.copy()\n')
            TEST.write('    master' + idx + '.allocate(args_master)\n')
            TEST.write('    instance_master' + idx + ' = master' + idx + '.exists()\n')
            TEST.write('    if instance_master' + idx + ':\n')
            TEST.write('        master' + idx + '.delete()\n')
            TEST.write('    master' + idx + '.create()\n')
            TEST.write('    master' + idx + '.open()\n')
            TEST.write('    master' + idx + '.replica.enableReplication(suffix=SUFFIX, ' +
                                            'role=REPLICAROLE_MASTER, ' +
                                            'replicaId=REPLICAID_MASTER_' + idx + ')\n\n')

        for idx in range(hubs):
            idx = str(idx + 1)
            TEST.write('    # Creating hub ' + idx + '...\n')
            TEST.write('    hub' + idx + ' = DirSrv(verbose=False)\n')
            TEST.write('    args_instance[SER_HOST] = HOST_HUB_' + idx + '\n')
            TEST.write('    args_instance[SER_PORT] = PORT_HUB_' + idx + '\n')
            TEST.write('    args_instance[SER_SERVERID_PROP] = SERVERID_HUB_' + idx + '\n')
            TEST.write('    args_hub = args_instance.copy()\n')
            TEST.write('    hub' + idx + '.allocate(args_hub)\n')
            TEST.write('    instance_hub' + idx + ' = hub' + idx + '.exists()\n')
            TEST.write('    if instance_hub' + idx + ':\n')
            TEST.write('        hub' + idx + '.delete()\n')
            TEST.write('    hub' + idx + '.create()\n')
            TEST.write('    hub' + idx + '.open()\n')
            TEST.write('    hub' + idx + '.replica.enableReplication(suffix=SUFFIX, ' +
                                            'role=REPLICAROLE_HUB, ' +
                                            'replicaId=REPLICAID_HUB_' + idx + ')\n\n')

        for idx in range(consumers):
            idx = str(idx + 1)
            TEST.write('    # Creating consumer ' + idx + '...\n')
            TEST.write('    consumer' + idx + ' = DirSrv(verbose=False)\n')
            TEST.write('    args_instance[SER_HOST] = HOST_CONSUMER_' + idx + '\n')
            TEST.write('    args_instance[SER_PORT] = PORT_CONSUMER_' + idx + '\n')
            TEST.write('    args_instance[SER_SERVERID_PROP] = SERVERID_CONSUMER_' + idx + '\n')
            TEST.write('    args_consumer = args_instance.copy()\n')
            TEST.write('    consumer' + idx + '.allocate(args_consumer)\n')
            TEST.write('    instance_consumer' + idx + ' = consumer' + idx + '.exists()\n')
            TEST.write('    if instance_consumer' + idx + ':\n')
            TEST.write('        consumer' + idx + '.delete()\n')
            TEST.write('    consumer' + idx + '.create()\n')
            TEST.write('    consumer' + idx + '.open()\n')
            TEST.write('    consumer' + idx + '.replica.enableReplication(suffix=SUFFIX, ' +
                                            'role=REPLICAROLE_CONSUMER, ' +
                                            'replicaId=CONSUMER_REPLICAID)\n\n')

        #
        # Create the master agreements
        #
        TEST.write('    #\n')
        TEST.write('    # Create all the agreements\n')
        TEST.write('    #\n')
        agmt_count = 0
        for idx in range(masters):
            master_idx = idx + 1
            for idx in range(masters):
                #
                # Create agreements with the other masters (master -> master)
                #
                idx += 1
                if master_idx == idx:
                    # skip ourselves
                    continue
                TEST.write('    # Creating agreement from master ' + str(master_idx) + ' to master ' + str(idx) + '\n')
                TEST.write("    properties = {RA_NAME:      r'meTo_$host:$port',\n")
                TEST.write("                  RA_BINDDN:    defaultProperties[REPLICATION_BIND_DN],\n")
                TEST.write("                  RA_BINDPW:    defaultProperties[REPLICATION_BIND_PW],\n")
                TEST.write("                  RA_METHOD:    defaultProperties[REPLICATION_BIND_METHOD],\n")
                TEST.write("                  RA_TRANSPORT_PROT: defaultProperties[REPLICATION_TRANSPORT]}\n")
                TEST.write('    m' + str(idx) + '_agmt = master' + str(master_idx) +
                            '.agreement.create(suffix=SUFFIX, host=master' +
                            str(idx) + '.host, port=master' + str(idx) + '.port, properties=properties)\n')
                TEST.write('    if not m' + str(idx) + '_agmt:\n')
                TEST.write('        log.fatal("Fail to create a master -> master replica agreement")\n')
                TEST.write('        sys.exit(1)\n')
                TEST.write('    log.debug("%s created" % m' + str(idx) + '_agmt)\n\n')
                agmt_count += 1

            for idx in range(hubs):
                idx += 1
                #
                # Create agreements from each master to each hub (master -> hub)
                #
                TEST.write('    # Creating agreement from master ' + str(master_idx) + ' to hub ' + str(idx) + '\n')
                TEST.write("    properties = {RA_NAME:      r'meTo_$host:$port',\n")
                TEST.write("                  RA_BINDDN:    defaultProperties[REPLICATION_BIND_DN],\n")
                TEST.write("                  RA_BINDPW:    defaultProperties[REPLICATION_BIND_PW],\n")
                TEST.write("                  RA_METHOD:    defaultProperties[REPLICATION_BIND_METHOD],\n")
                TEST.write("                  RA_TRANSPORT_PROT: defaultProperties[REPLICATION_TRANSPORT]}\n")
                TEST.write('    h' + str(idx) + '_agmt = master' + str(master_idx) +
                            '.agreement.create(suffix=SUFFIX, host=hub' +
                            str(idx) + '.host, port=hub' + str(idx) + '.port, properties=properties)\n')
                TEST.write('    if not h' + str(idx) + '_agmt:\n')
                TEST.write('        log.fatal("Fail to create a master -> hub replica agreement")\n')
                TEST.write('        sys.exit(1)\n')
                TEST.write('    log.debug("%s created" % h' + str(idx) + '_agmt)\n\n')
                agmt_count += 1

        #
        # Create the hub agreements
        #
        for idx in range(hubs):
            hub_idx = idx + 1
            #
            # Add agreements from each hub to each consumer (hub -> consumer)
            #
            for idx in range(consumers):
                idx += 1
                #
                # Create agreements from each hub to each consumer
                #
                TEST.write('    # Creating agreement from hub ' + str(hub_idx) + ' to consumer ' + str(idx) + '\n')
                TEST.write("    properties = {RA_NAME:      r'meTo_$host:$port',\n")
                TEST.write("                  RA_BINDDN:    defaultProperties[REPLICATION_BIND_DN],\n")
                TEST.write("                  RA_BINDPW:    defaultProperties[REPLICATION_BIND_PW],\n")
                TEST.write("                  RA_METHOD:    defaultProperties[REPLICATION_BIND_METHOD],\n")
                TEST.write("                  RA_TRANSPORT_PROT: defaultProperties[REPLICATION_TRANSPORT]}\n")
                TEST.write('    c' + str(idx) + '_agmt = hub' +
                            str(hub_idx) + '.agreement.create(suffix=SUFFIX, host=consumer' +
                            str(idx) + '.host, port=consumer' + str(idx) + '.port, properties=properties)\n')
                TEST.write('    if not c' + str(idx) + '_agmt:\n')
                TEST.write('        log.fatal("Fail to create a hub -> consumer replica agreement")\n')
                TEST.write('        sys.exit(1)\n')
                TEST.write('    log.debug("%s created" % c' + str(idx) + '_agmt)\n\n')
                agmt_count += 1

        if hubs == 0:
            #
            # No Hubs, see if there are any consumers to create agreements to...
            #
            for idx in range(masters):
                master_idx = idx + 1
                #
                # Create agreements with the consumers (master -> consumer)
                #
                for idx in range(consumers):
                    idx += 1
                    #
                    # Create agreements from each master to each consumer
                    #
                    TEST.write('    # Creating agreement fro master ' + str(master_idx) +
                               ' to consumer ' + str(idx) + '\n')
                    TEST.write("    properties = {RA_NAME:      r'meTo_$host:$port',\n")
                    TEST.write("                  RA_BINDDN:    defaultProperties[REPLICATION_BIND_DN],\n")
                    TEST.write("                  RA_BINDPW:    defaultProperties[REPLICATION_BIND_PW],\n")
                    TEST.write("                  RA_METHOD:    defaultProperties[REPLICATION_BIND_METHOD],\n")
                    TEST.write("                  RA_TRANSPORT_PROT: defaultProperties[REPLICATION_TRANSPORT]}\n")
                    TEST.write('    c' + str(idx) + '_agmt = master' + str(master_idx) +
                                '.agreement.create(suffix=SUFFIX, host=consumer' +
                                str(idx) + '.host, port=consumer' + str(idx) +
                                '.port, properties=properties)\n')
                    TEST.write('    if not c' + str(idx) + '_agmt:\n')
                    TEST.write('        log.fatal("Fail to create a hub -> consumer replica agreement")\n')
                    TEST.write('        sys.exit(1)\n')
                    TEST.write('    log.debug("%s created" % c' + str(idx) + '_agmt)\n\n')
                    agmt_count += 1

        #
        # Write the replication initializations
        #
        TEST.write('    #\n')
        TEST.write('    # Initialize all the agreements\n')
        TEST.write('    #\n')

        # Masters
        for idx in range(masters):
            idx += 1
            if idx == 1:
                continue
            TEST.write('    master1.agreement.init(SUFFIX, HOST_MASTER_' +
                       str(idx) + ', PORT_MASTER_' + str(idx) + ')\n')
            TEST.write('    master1.waitForReplInit(m' + str(idx) + '_agmt)\n')

        # Hubs
        consumers_inited = False
        for idx in range(hubs):
            idx += 1
            TEST.write('    master1.agreement.init(SUFFIX, HOST_HUB_' +
                   str(idx) + ', PORT_HUB_' + str(idx) + ')\n')
            TEST.write('    master1.waitForReplInit(h' + str(idx) + '_agmt)\n')
            for idx in range(consumers):
                if consumers_inited:
                    continue
                idx += 1
                TEST.write('    hub1.agreement.init(SUFFIX, HOST_CONSUMER_' +
                           str(idx) + ', PORT_CONSUMER_' + str(idx) + ')\n')
                TEST.write('    hub1.waitForReplInit(c' + str(idx) + '_agmt)\n')
            consumers_inited = True

        # Consumers (master -> consumer)
        if hubs == 0:
            for idx in range(consumers):
                idx += 1
                TEST.write('    master1.agreement.init(SUFFIX, HOST_CONSUMER_' +
                           str(idx) + ', PORT_CONSUMER_' + str(idx) + ')\n')
                TEST.write('    master1.waitForReplInit(c' + str(idx) + '_agmt)\n')

        TEST.write('\n')

        #
        # Write replicaton check
        #
        if agmt_count > 0:
            TEST.write('    #\n')
            TEST.write('    # Check replication is working...\n')
            TEST.write('    #\n')
            TEST.write("    REPL_TEST_DN = 'cn=test repl,' + SUFFIX\n")
            TEST.write('    master1.add_s(Entry((REPL_TEST_DN, {\n')
            TEST.write("                  'objectclass': 'top person'.split(),\n")
            TEST.write("                  'sn': 'test_repl',\n")
            TEST.write("                  'cn': 'test_repl'})))\n")
            TEST.write('    loop = 0\n')
            TEST.write('    ent = None\n')
            # Find the lowest replica type in the deployment(consumer -> master)
            if consumers > 0:
                replica = 'consumer1'
            elif hubs > 0:
                replica = 'hub1'
            else:
                replica = 'master2'
            TEST.write('    while loop <= 10:\n')
            TEST.write('        try:\n')
            TEST.write('            ent = ' + replica + '.getEntry(REPL_TEST_DN, ldap.SCOPE_BASE, "(objectclass=*)")\n')
            TEST.write('            break\n')
            TEST.write('        except ldap.NO_SUCH_OBJECT:\n')
            TEST.write('            time.sleep(1)\n')
            TEST.write('            loop += 1\n')
            TEST.write('    if ent is None:\n')
            TEST.write('        assert False\n')
            TEST.write('\n')

        #
        # Write the finals steps for replication
        #
        TEST.write('    # Clear out the tmp dir\n')
        TEST.write('    master1.clearTmpDir(__file__)\n\n')
        TEST.write('    return TopologyReplication(master1')
        for idx in range(masters):
            idx += 1
            if idx == 1:
                continue
            TEST.write(', master' + str(idx))
        for idx in range(hubs):
            TEST.write(', hub' + str(idx + 1))
        for idx in range(consumers):
            TEST.write(', consumer' + str(idx + 1))
        TEST.write(')\n')
    else:
        #
        # Standalone servers
        #

        # Args for the standalone instance
        for idx in range(instances):
            idx += 1
            if idx == 1:
                idx = ''
            else:
                idx = str(idx)
            TEST.write('    # Creating standalone instance ' + idx + '...\n')
            TEST.write('    standalone' + idx + ' = DirSrv(verbose=False)\n')
            TEST.write('    args_instance[SER_HOST] = HOST_STANDALONE' + idx + '\n')
            TEST.write('    args_instance[SER_PORT] = PORT_STANDALONE' + idx + '\n')
            TEST.write('    args_instance[SER_SERVERID_PROP] = SERVERID_STANDALONE' + idx + '\n')
            TEST.write('    args_standalone' + idx + ' = args_instance.copy()\n')
            TEST.write('    standalone' + idx + '.allocate(args_standalone' + idx + ')\n')

            # Get the status of the instance and restart it if it exists
            TEST.write('    instance_standalone' + idx + ' = standalone' + idx + '.exists()\n')

            # Remove the instance
            TEST.write('    if instance_standalone' + idx + ':\n')
            TEST.write('        standalone' + idx + '.delete()\n')

            # Create and open the instance
            TEST.write('    standalone' + idx + '.create()\n')
            TEST.write('    standalone' + idx + '.open()\n\n')

        TEST.write('    # Clear out the tmp dir\n')
        TEST.write('    standalone.clearTmpDir(__file__)\n')
        TEST.write('\n')
        TEST.write('    return TopologyStandalone(standalone')
        for idx in range(instances):
            idx += 1
            if idx == 1:
                continue
            TEST.write(', standalone' + str(idx))
        TEST.write(')\n')

    TEST.write('\n\n')

    #
    # Write the test function
    #
    TEST.write('def test_ticket' + ticket + '(topology):\n')
    TEST.write("    '''\n")
    if repl_deployment:
        TEST.write('    Write your replication testcase here.\n\n')
        TEST.write('    To access each DirSrv instance use:  topology.master1, topology.master2,\n' +
                   '        ..., topology.hub1, ..., topology.consumer1, ...\n')
    else:
        TEST.write('    Write your testcase here...\n')

    TEST.write("    '''\n\n")
    TEST.write("    log.info('Test complete')\n")
    TEST.write("\n\n")

    #
    # Write the final function here - delete each instance
    #
    TEST.write('def test_ticket' + ticket + '_final(topology):\n')
    if repl_deployment:
        for idx in range(masters):
            idx += 1
            TEST.write('    topology.master' + str(idx) + '.delete()\n')
        for idx in range(hubs):
            idx += 1
            TEST.write('    topology.hub' + str(idx) + '.delete()\n')
        for idx in range(consumers):
            idx += 1
            TEST.write('    topology.consumer' + str(idx) + '.delete()\n')
        TEST.write('\n\n')
    else:
        for idx in range(instances):
            idx += 1
            if idx == 1:
                idx = ''
            else:
                idx = str(idx)
            TEST.write('    topology.standalone' + idx + '.delete()\n')
        TEST.write('\n\n')
    TEST.write("    log.info('Testcase PASSED')\n")

    #
    # Write the main function
    #
    TEST.write('def run_isolated():\n')
    TEST.write('    global installation1_prefix\n')
    TEST.write('    installation1_prefix = None\n\n')
    TEST.write('    topo = topology(True)\n')
    TEST.write('    test_ticket' + ticket + '(topo)\n')
    TEST.write('    test_ticket' + ticket + '_final(topo)\n')
    TEST.write('\n\n')

    TEST.write("if __name__ == '__main__':\n")
    TEST.write('    run_isolated()\n\n')

    #
    # Done, close things up
    #
    TEST.close()
    print('Created: ' + filename)
