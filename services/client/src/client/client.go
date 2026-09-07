package client

import (
	"bufio"
	"os"
	"net"
	"time"
	"context"
	"errors"

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

func (client *Client) Run(ctx context.Context) error {
	defer client.conn.Close()

	file, err := os.Open(client.config.InputFile)
	if err != nil {
		return err
	}
	defer file.Close()

	if err := client.processBets(ctx, file); err != nil {
		return err
	}

	if err:= send_end(client.conn, uint8(client.config.AgencyId)); err != nil {
		logger.Error("send end", logger.Fail, "agency-id", client.config.AgencyId)
		return err
	}
	logger.Info("send end", logger.Success, "agency-id", client.config.AgencyId)

	winners, err := client.receiveWinners()
	if err != nil {
		return err
	}

	return client.writeWinners(winners)
}

func (client *Client) processBets(ctx context.Context, file *os.File) error {
	scanner := bufio.NewScanner(file)
	bets := make([]Bet, 0, client.config.BatchSize)
	for scanner.Scan() {
		select {
		case <-ctx.Done():
			return nil
		default:
		}
		bet, err := parse_bet(scanner.Text(), client.config.AgencyId)
		if err != nil {
			messageArgs := []any{"agency-id", client.config.AgencyId, "message", scanner.Text()}
			logger.Error("parse-bet", logger.Fail, messageArgs...)
			return err
		}
		bets = append(bets, bet)
		if len(bets) == client.config.BatchSize {
			if err := client.sendBatchAndWaitACK(bets); err != nil {
				return err
			}
			bets = bets[:0]
		}
	}
	if err := scanner.Err(); err != nil {
		return err
	}
	if len(bets) > 0 {
		return client.sendBatchAndWaitACK(bets)
	}
	return nil
}


func (client *Client) sendBatchAndWaitACK(bets []Bet) error {
	if err := send_batch(client.conn, bets); err != nil {
		logger.Error(
			"send-batch",
			logger.Fail,
			"agency-id",
			client.config.AgencyId,
		)
		return err
	}

	typeMessage, _, err := receive_message(client.conn)
	if err != nil {
		logger.Error(
			"receive-ack",
			logger.Fail,
			"agency-id",
			client.config.AgencyId,
		)
		return err
	}

	if typeMessage != ACK {
		logger.Error(
			"receive-ack",
			logger.Fail,
			"type-message", 
			typeMessage,
			"agency-id",
			client.config.AgencyId,
		)
		return errors.New("expected ACK")
	}

	logger.Info(
		"ACK received",
		logger.Success,
		"agency-id",
		client.config.AgencyId,
	)

	return nil
}

func (client *Client) receiveWinners() ([]Bet, error) {
	typeMessage, payload, err := receive_message(client.conn)
	if err != nil {
		logger.Error(
			"receive-winners",
			logger.Fail,
			"agency-id",
			client.config.AgencyId,
		)
		return nil, err
	}

	if typeMessage != WINNERS {
		logger.Error(
			"receive-winners",
			logger.Fail,
			"agency-id",
			client.config.AgencyId,
		)
		return nil, errors.New("expected WINNERS")
	}

	winners, err := deserialize_winners(payload)
	if err != nil {
		logger.Error(
			"deserialize-winners",
			logger.Fail,
			"agency-id",
			client.config.AgencyId,
		)
		return nil, err
	}

	logger.Info(
		"deserialize-winners",
		logger.Success,
		"agency-id",
		client.config.AgencyId,
	)

	return winners, nil
}

func (client *Client) writeWinners(winners []Bet) error {
	outputFile, err := os.OpenFile(
		client.config.OutputFile,
		os.O_APPEND|os.O_CREATE|os.O_WRONLY,
		0644,
	)
	if err != nil {
		logger.Error(
			"open-output-file",
			logger.Fail,
			"output-file",
			client.config.OutputFile,
		)
		return err
	}
	defer outputFile.Close()

	for _, winner := range winners {
		winnerString := unparse_bet(winner)

		if _, err := outputFile.WriteString(winnerString + "\n"); err != nil {
			logger.Error(
				"write-output-file",
				logger.Fail,
				"output-file",
				client.config.OutputFile,
			)
			return err
		}
	}

	logger.Info(
		"write-output-file",
		logger.Success,
		"winners received",
		winners,
	)

	return nil
}

func (client *Client) Close() {
	client.conn.Close()
}
