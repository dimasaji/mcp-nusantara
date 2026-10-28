// npm may launch the reviewed package test script; guards apply to its Node test child.
if(!process.argv[1]?.replaceAll('\\','/').endsWith('/npm-cli.js'))require('./test-write-guard.cjs');
