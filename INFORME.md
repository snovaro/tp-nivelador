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
    bet_number:       uint16
