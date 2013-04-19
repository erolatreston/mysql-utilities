#
# Copyright (c) 2013, Oracle and/or its affiliates. All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#

import mutlib
import rpl_admin
from mysql.utilities.exception import MUTLibError

_DEFAULT_MYSQL_OPTS_FILE = ('"--log-bin=mysql-bin --skip-slave-start '
                           '--log-slave-updates --gtid-mode=on '
                           '--enforce-gtid-consistency '
                           '--report-host=localhost --report-port=%s '
                           '--master-info-repository=file"')


class test(rpl_admin.test):
    """test replication administration commands
    This test runs the mysqlrpladmin utility on a known topology.
    It test the behavior of switchover demote master repository File
    Unrecoverable password. 

    Note: this test requires GTID enabled servers.
    """

    def check_prerequisites(self):
        if not self.servers.get_server(0).check_version_compat(5, 6, 9):
            raise MUTLibError("Test requires server version 5.6.9")
        return self.check_num_servers(1)

    def setup(self):
        self.res_fname = "result.txt"

        # Spawn servers
        self.server0 = self.servers.get_server(0)
        mysqld = _DEFAULT_MYSQL_OPTS_FILE % self.servers.view_next_port()
        self.server1 = self.spawn_server("rep_master_gtid", mysqld, True)
        mysqld = _DEFAULT_MYSQL_OPTS_FILE % self.servers.view_next_port()
        self.server2 = self.spawn_server("rep_slave1_gtid", mysqld, True)
        mysqld = _DEFAULT_MYSQL_OPTS_FILE % self.servers.view_next_port()
        self.server3 = self.spawn_server("rep_slave2_gtid", mysqld, True)
        mysqld = _DEFAULT_MYSQL_OPTS_FILE % self.servers.view_next_port()
        self.server4 = self.spawn_server("rep_slave3_gtid", mysqld, True)

        self.m_port = self.server1.port
        self.s1_port = self.server2.port
        self.s2_port = self.server3.port
        self.s3_port = self.server4.port

        rpl_admin.test.reset_topology(self)

        return True

    def run(self):
        test_num = 1

        master_conn = self.build_connection_string(self.server1).strip(' ')
        slave1_conn = self.build_connection_string(self.server2).strip(' ')
        slave2_conn = self.build_connection_string(self.server3).strip(' ')
        slave3_conn = self.build_connection_string(self.server4).strip(' ')

        comment = ("Test case %s - mysqlrplshow OLD Master before demote"
                   % test_num)
        cmd_str = "mysqlrplshow.py --master=%s " % master_conn
        cmd_opts = ["--discover-slaves=%s " % master_conn.split('@')[0]]
        res = self.run_test_case(0, "%s %s" % (cmd_str, "".join(cmd_opts)),
                                 comment)
        if not res:
            raise MUTLibError("%s: failed" % comment)

        test_num += 1
        # mysqlrpladmin --master=root:root@localhost:13091 
        # --new-master=root:root@localhost:13094 
        # --discover-slaves-login=root:root --demote-master  switchover 
        # --rpl-user=rpl:not-rpl-good-pass 
        comment = ("Test case %s - demote-master switchover "
                   "same user but different password given"
                   % test_num)
        cmd_str = "mysqlrpladmin.py --master=%s " % master_conn
        cmd_opts = [" --new-master=%s  " % slave1_conn,]
        cmd_opts.append("--discover-slaves=%s " % master_conn.split('@')[0])
        cmd_opts.append("--rpl-user=rpl:not-rpl-good-pass ")
        cmd_opts.append("--demote-master switchover ")
        cmd_opts.append("--no-health ")
        res = self.run_test_case(0, "%s %s" % (cmd_str, "".join(cmd_opts)),
                                 comment)
        if not res:
            raise MUTLibError("%s: failed" % comment)
        self.results.append("\n")

        test_num += 1
        # mysqlrpladmin --master=root:root@localhost:13091 
        # --new-master=root:root@localhost:13094 
        # --discover-slaves-login=root:root --demote-master  switchover 
        # --rpl-user=rpl --no-health
        comment = ("Test case %s - demote-master switchover "
                   "same user but missing password"
                   % test_num)
        cmd_str = "mysqlrpladmin.py --master=%s " % master_conn
        cmd_opts = [" --new-master=%s  " % slave1_conn,]
        cmd_opts.append("--discover-slaves=%s " % master_conn.split('@')[0])
        cmd_opts.append("--rpl-user=rpl ")
        cmd_opts.append("--demote-master switchover ")
        cmd_opts.append("--no-health ")
        res = self.run_test_case(0, "%s %s" % (cmd_str, "".join(cmd_opts)),
                                 comment)
        if not res:
            raise MUTLibError("%s: failed" % comment)
        self.results.append("\n")

        test_num += 1
        # mysqlrpladmin --master=root:root@localhost:13091 
        # --new-master=root:root@localhost:13094 
        # --discover-slaves-login=root:root --demote-master  switchover 
        # --rpl-user=not-rpl-user:not-rplpass --no-health
        comment = ("Test case %s - demote-master switchover "
                   "different user and password given"
                   % test_num)
        cmd_str = "mysqlrpladmin.py --master=%s " % master_conn
        cmd_opts = [" --new-master=%s  " % slave1_conn,]
        cmd_opts.append("--discover-slaves=%s " % master_conn.split('@')[0])
        cmd_opts.append("--rpl-user=not-rpl-user:not-rplpass ")
        cmd_opts.append("--demote-master switchover ")
        cmd_opts.append("--no-health ")
        res = self.run_test_case(0, "%s %s" % (cmd_str, "".join(cmd_opts)),
                                 comment)
        if not res:
            raise MUTLibError("%s: failed" % comment)
        self.results.append("\n")

        test_num += 1
        # mysqlrpladmin --master=root:root@localhost:13091 
        # --new-master=root:root@localhost:13094 
        # --discover-slaves-login=root:root --demote-master  switchover 
        # --rpl-user=not-rpl-user:not-rplpass --no-health --force 
        comment = ("Test case %s - demote-master switchover "
                   "different user and password given, now using the --force"
                   % test_num)
        cmd_str = "mysqlrpladmin.py --master=%s " % master_conn
        cmd_opts = [" --new-master=%s  " % slave1_conn,]
        cmd_opts.append("--discover-slaves=%s " % master_conn.split('@')[0])
        cmd_opts.append("--rpl-user=other_user:other_pass ")
        cmd_opts.append("--demote-master switchover ")
        cmd_opts.append(" --force --no-health")
        res = self.run_test_case(0, "%s %s" % (cmd_str, "".join(cmd_opts)),
                                 comment)
        if not res:
            raise MUTLibError("%s: failed" % comment)
        self.results.append("\n")

        test_num += 1
        comment = ("Test case %s - mysqlrplshow NEW Master." % test_num)
        cmd_str = "mysqlrplshow.py --master=%s " % slave1_conn
        cmd_opts = ["--discover-slaves=%s " % master_conn.split('@')[0]]
        res = self.run_test_case(0, "%s %s" % (cmd_str, "".join(cmd_opts)),
                                 comment)
        if not res:
            raise MUTLibError("%s: failed" % comment)

        test_num += 1
        # mysqlrpladmin --master=root:root@localhost:13091 
        # --new-master=root:root@localhost:13094 
        # --discover-slaves-login=root:root --demote-master  switchover 
        # --rpl-user=user_wopass --no-health --force 
        comment = ("Test case %s - demote-master switchover "
                   "different user and no password is given, now using the "
                   "--force" % test_num)
        cmd_str = "mysqlrpladmin.py --master=%s " % slave1_conn
        cmd_opts = [" --new-master=%s  " % slave2_conn,]
        cmd_opts.append("--discover-slaves=%s " % master_conn.split('@')[0])
        cmd_opts.append("--rpl-user=user_wopass ")
        cmd_opts.append("--demote-master switchover ")
        cmd_opts.append(" --force --no-health")
        res = self.run_test_case(0, "%s %s" % (cmd_str, "".join(cmd_opts)),
                                 comment)
        if not res:
            raise MUTLibError("%s: failed" % comment)
        self.results.append("\n")

        test_num += 1
        comment = ("Test case %s - mysqlrplshow NEW Master." % test_num)
        cmd_str = "mysqlrplshow.py --master=%s " % slave2_conn
        cmd_opts = ["--discover-slaves=%s " % master_conn.split('@')[0]]
        res = self.run_test_case(0, "%s %s" % (cmd_str, "".join(cmd_opts)),
                                 comment)
        if not res:
            raise MUTLibError("%s: failed" % comment)
        self.results.append("\n")

        test_num += 1
        # mysqlrpladmin --master=root:root@localhost:13091 
        # --new-master=root:root@localhost:13094 
        # --discover-slaves-login=root:root --demote-master  switchover 
        # --rpl-user=user_wopass --no-health
        comment = ("Test case %s - demote-master switchover "
                   "existing user with no password and no password is given"
                   % test_num)
        slaves = ",".join([master_conn, slave1_conn, slave3_conn])
        cmd_str = "mysqlrpladmin.py --master=%s " % slave2_conn
        cmd_opts = [" --new-master=%s  " % slave3_conn,]
        cmd_opts.append("--discover-slaves=%s " % master_conn.split('@')[0])
        cmd_opts.append("--rpl-user=user_wopass ")
        cmd_opts.append("--demote-master switchover ")
        cmd_opts.append("--no-health ")
        res = self.run_test_case(0, "%s %s" % (cmd_str, "".join(cmd_opts)),
                                 comment)
        if not res:
            raise MUTLibError("%s: failed" % comment)
        self.results.append("\n")

        test_num += 1
        comment = ("Test case %s - mysqlrplshow NEW Master." % test_num)
        cmd_str = "mysqlrplshow.py --master=%s " % slave3_conn 
        cmd_opts = ["--discover-slaves=%s " % master_conn.split('@')[0]]
        res = self.run_test_case(0, "%s %s" % (cmd_str, "".join(cmd_opts)),
                                 comment)
        if not res:
            raise MUTLibError("%s: failed" % comment)
        self.results.append("\n")

        # Now we return the topology to its original state for other tests
        rpl_admin.test.reset_topology(self)

        # Mask out non-deterministic data
        rpl_admin.test.do_masks(self)

        self.replace_result("# QUERY = SELECT "
                            "WAIT_UNTIL_SQL_THREAD_AFTER_GTIDS(",
                            "# QUERY = SELECT "
                            "WAIT_UNTIL_SQL_THREAD_AFTER_GTIDS(XXXXX)\n")
        self.replace_substring("localhost", "XXXXXXXXX")

        self.remove_result_and_lines_before("WARNING: There are slaves that "
                                            "had connection errors.")

        return True

    def get_result(self):
        return self.compare(__name__, self.results)

    def record(self):
        return self.save_result_file(__name__, self.results)

    def cleanup(self):
        return rpl_admin.test.cleanup(self)