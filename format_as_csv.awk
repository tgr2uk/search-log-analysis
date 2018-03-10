# reformat a query wfl to facilitate reading into Python as a dict

BEGIN { print "query,freq" }

{
    freq = $1
    sub(/ *[0-9]+ /, "");
    query = $0
    printf "%s,%d\n", query, freq
}
