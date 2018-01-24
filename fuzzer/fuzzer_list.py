fuzzers = {
    "Dumb":
    {
        "name": "Dumb",
        "file": "fuzzer_dumb.py",
        "args": '%(seed)s "%(input)s" %(output)s',
        "type": "mut"
    },
    "Radamsa":
    {
        "name": "Radamsa",
        "file": "radamsa/bin/radamsa",
        "args": '-s %(seed)s -o %(output)s "%(input)s"',
        "type": "mut"
    },
    "Zzuf":
    {
        "name": "Zzuf",
        "file": "zzuf/src/zzuf",
        "args": '-r 0.01 -s %(seed)s -v -d < "%(input)s" > %(output)s',
        "type": "mut"
    },
    "Dharma":
    {
        "name": "Dharma",
        "file": "dharma/dharma/dharma.py",
        "args": '-grammars %(grammar)s -seed %(seed)s > %(output)s',
        "type": "gen"
    }
}
