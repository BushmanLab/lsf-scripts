#!/usr/bin/env python
# This should work in Python 2.6+ and 3+

"""
Output a TSV table of LSF job information for a given user group.

Example:

$ ./jobs_for_group.py usergroup
NJobs   MaxDays User
17      6       a_user
0               somebodyelse
1       0       somebodyelse2
"""

import sys
import csv
import grp
import datetime
import subprocess

BJOBS_CMD = "bjobs"

def summarize_jobs_for(user):
    """Create dict for all LSF jobs for the given user."""
    cmd_args = [BJOBS_CMD, "-u", user]
    p = subprocess.Popen(cmd_args,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
    stdout, stderr = p.communicate()
    lines = [line.strip() for line in stdout.split("\n")[1:]]
    # TODO what happens when a job datestamp crosses a year?
    year = datetime.datetime.now().year
    times = ["%d %s" % (year, line[71:83]) for line in lines if line]
    times = [datetime.datetime.strptime(t, "%Y %b %d %H:%M") for t in times]
    now = datetime.datetime.now()
    num = len(times)
    if num:
        oldest_days = (now - sorted(times)[0]).days
    else:
        oldest_days = None
    return({"NJobs": num, "MaxDays": oldest_days, "User": user})

def tabulate_jobs_for(users):
    """Create list of dicts for all LSF jobs across the given users."""
    tbl = [summarize_jobs_for(user) for user in users]
    sort = lambda row: [-(row["NJobs"] or 0)*(row["MaxDays"] or 0), row["User"]]
    tbl = sorted(tbl, key = sort)
    return(tbl)

def report_jobs_table(tbl, f=sys.stdout):
    """Write TSV text version of list of job summaries."""
    fields = ["NJobs", "MaxDays", "User"]
    writer = csv.DictWriter(f, delimiter = "\t", fieldnames = fields)
    # special handling for Python 2.6
    # https://stackoverflow.com/a/2982117
    # https://stackoverflow.com/a/21069676
    try:
        writer.writeheader()
    except AttributeError:
        headers = dict((h, h) for h in fields)
        writer.writerow(headers)
    writer.writerows(tbl)

def main(args=sys.argv):
    """Write TSV report of job information for all users in given group."""
    if len(args) != 2:
        sys.stderr.write("Usage: %s group-name\n" % __file__)
        sys.exit(1)
    group_name = args[1]
    try:
        group_entry = grp.getgrnam(group_name)
    except KeyError:
        sys.stderr.write("Group not found: %s-name\n" % group_name)
        sys.exit(1)
    group_members = group_entry.gr_mem
    tbl = tabulate_jobs_for(group_members)
    report_jobs_table(tbl)

if __name__ == "__main__":
    main()
