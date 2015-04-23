DNS Service
===========

Code for America’s DNS host records change frequently, with subdomains added
regularly for various projects. This is a master copy of our domain name
collection. We’d like to keep it in Git now to maintain an ongoing historical
record of changes and older versions to allow for easier edit access and
rollback.

If you need to add a new DNS record to codeforamerica.org, edit the file
[`host-records.csv`](host-records.csv) and submit a pull request via Github.
Records should be live within a few minutes depending on speed of Travis
and Heroku. Check with [whatsmydns.net](https://www.whatsmydns.net).

Code
----

![Build status](https://travis-ci.org/codeforamerica/DNS-Service.svg)

DNS-Service is a [Python + Flask app](https://github.com/codeforamerica/howto/blob/master/Python-Virtualenv.md).
Required packages can be found in [`requirements.txt`](requirements.txt),
and process descriptions can be found in [`Procfile`](Procfile) for
[Procfile-based deployment](https://github.com/codeforamerica/howto/blob/master/Procfile.md).

Validity of host records and access to our DNS service is checked at app start
time; subsequent web requests are useful only for diagnostics.

Two environment variables are required for use:

* `DNS_API_BASE` - Base URL for DNS service API.
* `DNS_API_KEY` - Secret key for DNS service API.

Tests can be run with:

    python -m cfa_dns.test
