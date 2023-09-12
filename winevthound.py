#! /usr/bin/env python3
import pandas as pd

def generate_computer(computer_fqdn, computer_sid, user_sids, admin_sids, rdp_sids):
    """Generate JSON for a computer object that contains group memberships and sessions
    
    Keyword arguments:
    computer_fqdn -- FQDN of the computer
    computer_sid -- SID of the computer
    user_sids -- SIDs of users that had sessions on the computer
    admin_sids -- SIDs of users that had Admin privileges on the computer
    rdp_sids -- SIDs of users that logged onto the computer via RDP
    """
    domain = '.'.join(computer_fqdn.split('.')[1:]).upper()
    sessions = generate_sessions(computer_sid, user_sids)
    localgroups = generate_localgroups(computer_fqdn, computer_sid, admin_sids, rdp_sids)

    return f"""{{"Properties":{{"domain":"{domain}","name":"{computer_fqdn.upper()}"}},{sessions},{localgroups},"ObjectIdentifier":"{computer_sid}"}}"""


def generate_sessions(computer_sid, user_sids):
    """ Generate JSON containing all user sessions for the given computer

    Keyword arguments:
    computer_sid -- The SID of the computer that has user sessions
    user_sids -- List of SIDs of all users that had a session to the computer
    """
    sessions = []
    for i, user_sid in enumerate(user_sids):
        # generate session object for each user
        sessions.append(generate_session(computer_sid, user_sid))

    return f""""Sessions":{{"Results":[{','.join(sessions)}],"Collected":true,"FailureReason":null}}"""


def generate_session(computer_sid, user_sid):
    """Generate JSON for a logon session

    user_sid -- SID of the user who logged on
    computer_sid -- SID of the computer the user logged onto
    """
    return f"""{{"UserSID":"{user_sid}","ComputerSID":"{computer_sid}"}}"""


def generate_localgroups(computer_fqdn, computer_sid, admin_sids, rdp_sids):
    """Generates JSON for local group memberships in ADMINISTRATORS and REMOTE DESKTOP USERS

    Keyword arguments:
    computer_fqdn -- FQDN of the computer the group memberships are from
    computer_sid -- SID of the computer the group memberships are from
    admin_sids -- SIDs of users that are members of ADMINISTRATORS
    rdp_sids -- SIDS of users that are members of REMOTE DESKTOP USERS
    """
    admins = generate_localgroup("ADMINISTRATORS", "544", computer_fqdn, computer_sid, admin_sids)
    rdp = generate_localgroup("REMOTE DESKTOP USERS", "555", computer_fqdn, computer_sid, rdp_sids)

    return f""""LocalGroups":[{admins},{rdp}]"""


def generate_localgroup(group_name, group_rid, computer_fqdn, computer_sid, user_sids):
    """Generate JSON for a group based on group memberships

    Keyword arguments:
    group_name -- Name of the group
    group_rid -- RID of the group
    computer_fqdn -- FQDN of the computer the group memberships are from
    computer_sid -- SID of the computer the group memberships are from
    user_sids -- SIDs of users that are members of the group
    """
    memberships = []
    for i, user_sid in enumerate(user_sids):
        # generate session object for each user
        memberships.append(generate_group_membership(user_sid))

    return f"""{{"ObjectIdentifier":"{computer_sid}-{group_rid}","Name":"{group_name.upper()}@{computer_fqdn.upper()}","Results":[{','.join(memberships)}],"LocalNames":[],"Collected": true,"FailureReason":null}}"""


def generate_group_membership(user_sid):
    """Generate JSON for group membership
    
    Keyword arguments:
    user_sid -- SID of user who is in group
    """
    return f"""{{"ObjectIdentifier":"{user_sid}","ObjectType":"User"}}"""


def main():
    """main function"""
    # read input files
    sid_lookup = pd.read_csv('computerSids.csv')
    logons = pd.read_csv('sessions.csv')
    admins = pd.read_csv('admins.csv')
    rdp = pd.read_csv('rdp.csv')

    # outer join all session tables
    # within our log time frame, we might not see admin/rdp logons for a computer
    # hence, some of the columns might be empty
    merged = pd.merge(logons, admins, on='DNSHostName', how='outer').fillna(value='')
    merged = pd.merge(merged, rdp, on='DNSHostName', how='outer').fillna(value='')

    # inner join computer sids
    # we can only generate json output, if we have the computer sid
    merged = merged.merge(sid_lookup, on='DNSHostName')

    meta = f""" "meta": {{"methods":266,"type":"computers","count":{len(merged)},"version":5}}"""

    computers = []
    for i, line in merged.iterrows():
        # extract values from merged table
        computer_sid = line['SID']
        computer = line['DNSHostName']
        session_sids = line['Sessions'].split()
        admin_sids = line['Admins'].split()
        rdp_sids = line['RDP'].split()

        # generate computer object and add it to list
        computers.append(generate_computer(computer, computer_sid, session_sids, admin_sids, rdp_sids))

    #output final JSON
    print(f"""{{"data":[{','.join(computers)}],{meta}}}""")

if __name__ == "__main__":
    main()
