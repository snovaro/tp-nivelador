package client

import (
	"bufio"
	"os"
	"net"
	"time"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/logger"
)

const CONNECTION_ATTEMPTS_MAX = 3
const CONNECTION_ATTEMPS_DELAY_MS = 200

const ECHO_CLIENT_BUFFER_SIZE = 512
const ECHO_CLIENT_MESSAGE_AMOUNT = 3
const ECHO_CLIENT_MESSAGE_DELAY_MS = 1000

type ClientConfig struct {
	ServerHost string
	ServerPort string
	AgencyId   string
	InputFile  string
	OutputFile string
}

type Client struct {
	conn   net.Conn
	config ClientConfig
}

func NewClient(config ClientConfig) (*Client, error) {
	conn, err := connectToServer(config.ServerHost, config.ServerPort)
	if err != nil {
		logger.Warn("connect-to-server", logger.Fail)
		return nil, err
	}

	client := &Client{conn: conn, config: config}
	return client, nil
}

func connectToServer(host, port string) (net.Conn, error) {
	const action = "connect-to-server"
	var err error
	var conn net.Conn

	logger.Info(action, logger.InProgress)
	for i := range CONNECTION_ATTEMPTS_MAX {
		conn, err = net.Dial("tcp", host+":"+port)
		if err != nil {
			logger.Warn(action, logger.Fail, "attempt", i)
			time.Sleep(CONNECTION_ATTEMPS_DELAY_MS * time.Millisecond)
			continue
		}

		logger.Info(action, logger.Success)
		break
	}

	return conn, err
}

func (client *Client) Run() error {
	const mainAction = "test-echo-server"
	defer client.conn.Close()
	file, err := os.Open(client.config.InputFile)
	if err != nil {
		return err
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)

	for scanner.Scan() {
		clientMessage := scanner.Text()
		messageArgs := []any{"agency-id", client.config.AgencyId, "message", clientMessage}
		logger.Info(mainAction, logger.InProgress, messageArgs...)
		bet, err := parse_bet(clientMessage, client.config.AgencyId)
		if err != nil {
			logger.Error(mainAction, logger.Fail, messageArgs...)
			return err
		}

		if err := send_bet(client.conn, bet); err != nil {
			logger.Error(mainAction, logger.Fail, messageArgs...)
			return err
		}

		/* responseBuffer, err := safe_socket.RecvAll(client.conn, len(clientMessage))
		if err != nil {
			logger.Error("recv-response", logger.Fail, messageArgs...)
			return err
		}

		if string(responseBuffer) != clientMessage {
			logger.Error("check-response", logger.Fail, messageArgs...)
			return err
		}
		outputFile, err := os.OpenFile(client.config.OutputFile, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
		if err != nil {
			logger.Error("open-output-file", logger.Fail, messageArgs...)
			return err
		}
		defer outputFile.Close()

		if _, err := outputFile.WriteString(clientMessage + "\n"); err != nil {
			logger.Error("write-output-file", logger.Fail, messageArgs...)
			return err
		} */

		logger.Info(mainAction, logger.Success, messageArgs...)


	}
	logger.Info(mainAction, logger.Success, "agency-id", client.config.AgencyId)

	return nil
}
