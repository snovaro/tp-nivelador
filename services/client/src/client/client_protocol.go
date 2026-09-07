package client

import (
	"encoding/binary"
	"fmt"
	"net"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/logger"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/safe_socket"
)

func send_bet(conn net.Conn, bet Bet) error {
	const action = "send-bet"
	logger.Info(action, logger.InProgress, "sending bet", bet)
	payload, err := serialize_bet(bet)
	if err != nil {
		logger.Error(action, logger.Fail, "bet", bet)
		return err
	}
	if err := send_message(conn, BET, payload); err != nil {
		logger.Error(action, logger.Fail, "bet", bet)
		return err
	}
	logger.Info(action, logger.Success, "bet sent", bet)
	return nil
}

func serialize_bet(bet Bet) ([]byte, error) {
	logger.Info("serialize_bet", logger.InProgress, "serializing bet", bet)
	agencyId := uint8(bet.AgencyId)
	nameBytes := []byte(bet.Name)
	if len(nameBytes) > 255 {
		return nil, fmt.Errorf("name too long: %d bytes", len(nameBytes))
	}
	surnameBytes := []byte(bet.Surname)
	if len(surnameBytes) > 255 {
		return nil, fmt.Errorf("surname too long: %d bytes", len(surnameBytes))
	}
	dniBytes := make([]byte, 4)
	binary.BigEndian.PutUint32(dniBytes, bet.DNI)
	yearBytes := make([]byte, 2)
	binary.BigEndian.PutUint16(yearBytes, bet.Year)
	month := uint8(bet.Month)
	day := uint8(bet.Day)
	betNumberBytes := make([]byte, 2)
	binary.BigEndian.PutUint16(betNumberBytes, bet.BetNumber)
	payload := build_bet_payload(agencyId, nameBytes, surnameBytes, dniBytes, yearBytes, month, day, betNumberBytes)

	logger.Info("serialize_bet", logger.Success, "bet serialized", bet)
	return payload, nil
}

func build_bet_payload(agencyId uint8, nameBytes, surnameBytes, dniBytes, yearBytes []byte, month, day uint8, betNumberBytes []byte) []byte {
	var payload []byte
	payload = append(payload, agencyId)
	payload = appendString(payload, string(nameBytes))
	payload = appendString(payload, string(surnameBytes))
	payload = append(payload, dniBytes...)
	payload = append(payload, yearBytes...)
	payload = append(payload, month)
	payload = append(payload, day)
	payload = append(payload, betNumberBytes...)
	return payload
}

func appendString(payload []byte, value string) []byte {
	bytes := []byte(value)
	payload = append(payload, uint8(len(bytes)))
	payload = append(payload, bytes...)
	return payload
}

func send_message(conn net.Conn, typeMessage int, payload []byte) error {
	logger.Info("send_message", logger.InProgress, "sending message", typeMessage)
	var header [3]byte
	header[0] = byte(typeMessage)
	if len(payload) > 65535 {
		return fmt.Errorf("payload too large: %d bytes", len(payload))
	}
	binary.BigEndian.PutUint16(header[1:], uint16(len(payload)))
	message := append(header[:], payload...)
	if err := safe_socket.SendAll(conn, message); err != nil {
		logger.Error("send_message", logger.Fail, "message", typeMessage)
		return err
	}
	logger.Info("send_message", logger.Success, "message sent", typeMessage)
	return nil
}

func receive_message(conn net.Conn) (byte, []byte, error) {
	logger.Info("receive_message", logger.InProgress, "receiving message")
	header, err := safe_socket.RecvAll(conn, 3)
	if err != nil {
		logger.Error("receive_header", logger.Fail)
		return 0, nil, err
	}
	typeMessage := header[0]
	payloadSize := binary.BigEndian.Uint16(header[1:])
	payload, err := safe_socket.RecvAll(conn, int(payloadSize))
	if err != nil {
		logger.Error("receive_payload", logger.Fail)
		return 0, nil, err
	}
	logger.Info("receive_message", logger.Success, "message received", typeMessage)
	return typeMessage, payload, nil
}

func send_end(conn net.Conn, agencyId uint8) error {
	const action = "send-end"
	logger.Info(action, logger.InProgress, "sending end message")
	if err := send_message(conn, END, []byte{agencyId}); err != nil {
		logger.Error(action, logger.Fail)
		return err
	}
	logger.Info(action, logger.Success, "end message sent")
	return nil
}

func deserialize_winners(payload []byte) ([]Bet, error) {
	logger.Info("deserialize_winners", logger.InProgress, "deserializing winners")
	var winners []Bet
	offset := 0
	for offset < len(payload) {
		bet, bytesRead, err := deserialize_bet(payload[offset:])
		if err != nil {
			logger.Error("deserialize_winners", logger.Fail)
			return nil, err
		}
		winners = append(winners, bet)
		offset += bytesRead
	}
	logger.Info("deserialize_winners", logger.Success, "winners deserialized")
	return winners, nil
}

func deserialize_bet(payload []byte) (Bet, int, error) {
	logger.Info("deserialize_bet", logger.InProgress, "deserializing bet")
	offset := 0

	agencyId := payload[offset]
	offset++

	nameLength := int(payload[offset])
	offset++
	name := string(payload[offset : offset+nameLength])
	offset += nameLength

	surnameLength := int(payload[offset])
	offset++
	surname := string(payload[offset : offset+surnameLength])
	offset += surnameLength

	dni := binary.BigEndian.Uint32(payload[offset : offset+4])
	offset += 4

	year := binary.BigEndian.Uint16(payload[offset : offset+2])
	offset += 2

	month := payload[offset]
	offset++

	day := payload[offset]
	offset++

	betNumber := binary.BigEndian.Uint16(payload[offset : offset+2])
	offset += 2

	bet := Bet{
		AgencyId:  uint8(agencyId),
		Name:	 name,
		Surname:   surname,
		DNI:       dni,
		Year:      year,
		Month:     month,
		Day:       day,
		BetNumber: betNumber,
	}
	return bet, offset, nil
}

func serialize_bets(bets []Bet) ([]byte, error) {
	logger.Info("serialize_bets", logger.InProgress, "serializing bets", bets)
	var payload []byte
	for _, bet := range bets {
		betPayload, err := serialize_bet(bet)
		if err != nil {
			logger.Error("serialize_bets", logger.Fail, "bet", bet)
			return nil, err
		}
		payload = append(payload, betPayload...)
	}
	logger.Info("serialize_bets", logger.Success, "bets serialized", bets)
	return payload, nil
}

func send_batch(conn net.Conn, bets []Bet) error {
	typeMessage := BATCH
	payload, err := serialize_bets(bets)
	if err != nil {
		return err
	}
	if err := send_message(conn, typeMessage, payload); err != nil {
		return err
	}
	return nil
	
}