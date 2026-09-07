# TP Nivelador — Informe

## 1. Introducción

El sistema implementado consiste en un servidor que recibe apuestas provenientes de distintas agencias concurrentemente, procesa las apuestas recibidas y realiza sorteos cuando se cumplen las condiciones establecidas por el sistema.

La solución utiliza comunicación mediante sockets TCP y permite que múltiples clientes (agencias) se conecten y envíen sus apuestas de manera concurrente. El servidor coordina la ejecución de los distintos clientes mediante mecanismos de sincronización, garantizando que el sorteo se realice únicamente cuando se cumplen las condiciones necesarias.

---

## 2. Protocolo de comunicación

La comunicación entre clientes y servidor se realiza mediante **TCP**.

Todos los valores numéricos del protocolo utilizan **Big Endian (Network Byte Order)** y los strings se codifican utilizando **UTF-8**.

### 2.1. Message Header

Cada mensaje comienza con un encabezado compuesto por:

| Campo    |  Tamaño |
| -------- | ------: |
| `type`   |  1 byte |
| `length` |  2 bytes |

* `type` identifica el tipo de mensaje.
* `length` indica la longitud del payload del mensaje.

### 2.2. Tipos de mensajes

El protocolo define los siguientes tipos:

| Valor  | Mensaje | Descripción                                                          |
| ------ | ------- | -------------------------------------------------------------------- |
| `0x01` | `BET`   | Contiene una apuesta realizada por un cliente.                       |
| `0x02` | `END`   | Indica que la agencia terminó de enviar sus apuestas.                |
| `0x03` | `ACK`   | Confirmación de recepción de un mensaje de tipo `BET` o `BATCH` del servidor hacia el cliente.        |
| `0x04` | `WINNERS` | Contiene la lista de ganadores de un sorteo.                        |
| `0x05` | `BATCH` | Contiene un lote de apuestas.                                        |

### 2.3. Payload de una apuesta

El payload de un mensaje `BET` contiene los datos necesarios para representar una apuesta:

| Campo            | Tipo / Tamaño |
| ---------------- | ------------: |
| `agency_length`  |       `uint8` |
| `agency_id`      |     `K bytes` |
| `name_length`    |       `uint8` |
| `name`           |     `N bytes` |
| `surname_length` |       `uint8` |
| `surname`        |     `M bytes` |
| `dni`            |      `uint32` |
| `year`           |      `uint16` |
| `month`          |       `uint8` |
| `day`            |       `uint8` |
| `bet_number`     |      `uint32` |

Los campos de longitud permiten determinar cuántos bytes corresponden a cada string dentro del mensaje, evitando depender de terminadores especiales.


El payload de un mensaje `BATCH` contiene un conjunto de apuestas, cada una con la misma estructura que la definida para el mensaje `BET`. La cantidad de apuestas en el batch se determina a partir de la variable de entorno `BATCH_SIZE`.


---

## 3. Comunicación entre clientes y servidor

Cada agencia se ejecuta como un cliente independiente y establece una conexión TCP con el servidor.

Una vez establecida la conexión, el cliente envía sus apuestas al servidor. Para reducir la cantidad de mensajes y aprovechar la comunicación por bloques, las apuestas pueden enviarse agrupadas en **batches**.

El tamaño del batch es configurable. Una vez alcanzado dicho tamaño, el cliente envía el conjunto de apuestas al servidor y espera la confirmación correspondiente antes de continuar.

Al finalizar el archivo de entrada, el cliente envía un mensaje `FIN`, indicando que ya no enviará más apuestas.

Luego del procesamiento y sorteo correspondiente, el servidor envía los ganadores al cliente, que los deserializa y escribe en su archivo de salida.

---

## 4. Concurrencia y sincronización

El servidor debe atender múltiples agencias simultáneamente. Para esto, cada cliente conectado es procesado de manera concurrente, permitiendo que distintas agencias puedan enviar sus apuestas sin bloquearse mutuamente.

Para coordinar la ejecución concurrente se utiliza una estructura `ServerState`, que mantiene el estado compartido necesario para controlar el avance del sistema.

Esta estructura utiliza una **conditional variable**, mediante la cual los hilos asociados a los clientes pueden esperar hasta que se cumplan las condiciones necesarias para realizar un sorteo.

### 4.1. Quórum

Una de las condiciones necesarias para realizar un sorteo es alcanzar el **quórum de agencias** correspondiente.

Los clientes que ya terminaron de enviar sus apuestas pueden quedar esperando en la condición correspondiente hasta que se alcance dicho quórum.

La condition variable permite que estos hilos permanezcan bloqueados sin consumir CPU mientras esperan que cambie el estado del servidor. Cuando se cumple la condición, el hilo correspondiente puede continuar con la ejecución del sorteo.

### 4.2. Agencias que todavía están enviando apuestas

Además del quórum, tome la decision de diseño de garantizar que no haya agencias que todavía estén enviando apuestas al momento de realizar el sorteo.

Por este motivo, el estado compartido también permite controlar qué agencias continúan activas y cuáles ya finalizaron su envío de apuestas.

De esta manera, el sorteo no se realiza mientras existan agencias que todavía puedan incorporar nuevas apuestas al conjunto correspondiente.

---

## 5. Manejo de nuevos clientes y nuevos sorteos

El servidor contempla también el caso en el que una agencia se conecta luego de que ya se realizó un sorteo.

En este escenario, el cliente no debe incorporarse al sorteo que ya finalizó. En su lugar, la llegada de una nueva agencia da lugar a un nuevo estado de ejecución (`ServerState`), asociado al siguiente sorteo.

La idea general es separar los distintos sorteos en estados independientes:

```text
             ServerState
                  │
        ┌─────────┴─────────┐
        │                   │
   Agencias             Condiciones
        │                   │
        └───────┬───────────┘
                │
             Quórum
                │
                ▼
             Sorteo
                │
                ▼
          Nuevo estado
       para el siguiente
             sorteo
```

Esto permite que un cliente que llega después de finalizado un sorteo no modifique el resultado de dicho sorteo y deba esperar las condiciones correspondientes al siguiente.

---

## 6. Batching

La implementación soporta el envío de apuestas agrupadas en batches.

El cliente acumula apuestas hasta alcanzar el tamaño configurado y luego transmite el conjunto como una única operación de envío. Después de enviar el batch, espera el `ACK` del servidor antes de continuar con el siguiente.

También se contempla el caso en el que la cantidad total de apuestas no sea múltiplo del tamaño del batch. En ese caso, las apuestas restantes se envían como un último batch antes de finalizar la comunicación.

---

## 7. Manejo de errores y finalización

El cliente y el servidor verifican los errores producidos durante las operaciones de comunicación, lectura y escritura.

El cliente también maneja la finalización mediante `context.Context`, permitiendo interrumpir su ejecución cuando el contexto es cancelado.

Asimismo, se garantiza el cierre de las conexiones y archivos abiertos mediante mecanismos de limpieza de recursos.

---

## 8. Resultados de los tests

La implementación fue validada utilizando la suite de tests provista por la cátedra.

Resultado de la ejecución de:

```bash
make test
```

```text
Testing json import.....................OK

Testing forced exit.....................OK

Testing winners list in output files....OK

Testing spawned processes/threads.......OK

Testing memory profile..................OK

Testing sigterm handling................OK

Testing client short read/write.........OK

Testing server short read/write.........OK

Testing batching........................OK
```

Todos los tests finalizaron correctamente.


---

## 9. Conclusión

La solución implementada permite la comunicación concurrente entre múltiples agencias y el servidor mediante TCP, utilizando un protocolo binario con mensajes estructurados.

El uso de batches permite agrupar múltiples apuestas en una misma operación de comunicación, mientras que el mecanismo de sincronización basado en `ServerState` y conditional variables permite coordinar a los distintos clientes y garantizar que los sorteos se realicen únicamente cuando se cumplen las condiciones establecidas.

Finalmente, la solución fue validada mediante la suite de tests de la cátedra, obteniendo resultados satisfactorios en todos los casos.
