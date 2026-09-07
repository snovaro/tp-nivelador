Redactar un breve informe en donde se detallen los aspectos más importantes de la solución provista, como ser el protocolo de comunicación implementado y los mecanismos para sincronizar la ejecución concurrente.

Protocolo de comunicación implementado:

Byte order: Big Endian
Strings: UTF-8

MESSAGE HEADER
    type:   1 byte
    length: 2 bytes 

MESSAGE TYPES
    0x01 START
    0x02 BET
    0x03 FIN
    0x04 ERROR

BET PAYLOAD
    agency_length:    uint8
    agency_id:        K bytes
    name_length:      uint8
    name:             N bytes
    surname_length:   uint8
    surname:          M bytes
    dni:              uint32
    year:             uint16
    month:            uint8
    day:              uint8
    bet_number:       uint32


Mi idea de started_client es que no se haga el sorteo si hay agencias enviando apuestas.  Y que si ya se hizo el sorteo cuando entra un cliente salte la excepcion y se cree un nuevo state para esa nueva agencia, que tenga que esperar quorum para el nuevo sorteo


santi@fedora:~/Desktop/FIUBA/Distri-I/tp-nivelador$ make test
rm failed_test.log -f
PYTHONPATH="/home/santi/Desktop/FIUBA/Distri-I/tp-nivelador" python3 tests/run.py
Testing json import.....................OK
Testing forced exit.....................OK
Testing winners list in output files....OK
Testing spawned processes/threads.......OK
Testing memory profile..................OK
Testing sigterm handling................OK
Testing client short read/write.........OK
Testing server short read/write.........OK
Testing batching........................OK