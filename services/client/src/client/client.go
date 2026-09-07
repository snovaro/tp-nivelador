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


type ClientConfig struct {
	ServerHost string
	ServerPort string
	AgencyId   int
	InputFile  string
	OutputFile string
	BatchSize  int
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
	defer client.conn.Close()
	file, err := os.Open(client.config.InputFile)
	if err != nil {
		return err
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	bets := make([]Bet, 0, client.config.BatchSize)

	for scanner.Scan() {
		clientMessage := scanner.Text()
		messageArgs := []any{"agency-id", client.config.AgencyId, "message", clientMessage}
		logger.Info("parse-bet", logger.InProgress, messageArgs...)
		bet, err := parse_bet(clientMessage, client.config.AgencyId)

		if err != nil {
			logger.Error("parse-bet", logger.Fail, messageArgs...)
			return err
		}

		bets = append(bets, bet)

		if len(bets) < client.config.BatchSize {
			continue
		}

		if err := send_batch(client.conn, bets); err != nil {
			logger.Error("send-batch", logger.Fail, messageArgs...)
			return err
		}

		bets = bets[:0]

		typeMessage, _, err := receive_message(client.conn)
		if err != nil {
			logger.Error("receive-message", logger.Fail, messageArgs...)
			return err
		}
		if typeMessage != ACK {
			logger.Error("receive-message", logger.Fail, messageArgs...)
			return err
		}
		logger.Info("ACK received", logger.Success, messageArgs...)

	}

	if len(bets) > 0 {
		if err := send_batch(client.conn, bets); err != nil {
			logger.Error("send-batch", logger.Fail, "agency-id", client.config.AgencyId)
			return err
		}
		typeMessage, _, err := receive_message(client.conn)
		if err != nil {
			logger.Error("receive-message", logger.Fail, "agency-id", client.config.AgencyId)
			return err
		}
		if typeMessage != ACK {
			logger.Error("receive-message", logger.Fail, "agency-id", client.config.AgencyId)
			return err
		}
		logger.Info("ACK received", logger.Success, "agency-id", client.config.AgencyId)
	}
	logger.Info("send end", logger.Success, "agency-id", client.config.AgencyId)
	if err:= send_end(client.conn, uint8(client.config.AgencyId)); err != nil {
		logger.Error("send end", logger.Fail, "agency-id", client.config.AgencyId)
		return err
	}

	typeMessage, payload, err := receive_message(client.conn)
	if err != nil {
		logger.Error("receive-winners", logger.Fail, "agency-id", client.config.AgencyId)
		return err
	}
	if typeMessage != WINNERS {
		logger.Error("receive-winners", logger.Fail, "agency-id", client.config.AgencyId)
		return err
	}

	winners, err := deserialize_winners(payload)
	logger.Info("deserialize-winners", logger.Success, "agency-id", client.config.AgencyId)
	if err != nil {
		logger.Error("receive-winners", logger.Fail, "agency-id", client.config.AgencyId)
		return err
	}
	outputFile, err := os.OpenFile(client.config.OutputFile, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
		if err != nil {
			logger.Error("open-output-file", logger.Fail, "output-file", client.config.OutputFile)
			return err
		}
	defer outputFile.Close()

	for _, winner := range winners {
		winnerString := unparse_bet(winner)
		if _, err := outputFile.WriteString(winnerString + "\n"); err != nil {
			logger.Error("write-output-file", logger.Fail, "output-file", client.config.OutputFile)
			return err
		}
	}

	logger.Info("write-output-file", logger.Success, "winners received", winners)
	return nil
}
