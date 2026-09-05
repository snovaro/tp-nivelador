func send_bet(conn net.Conn, bet Bet) error {
	const action = "send-bet"
	logger.Info(action, logger.InProgress, "sending bet", bet)
	payload, err := serialize_bet(bet)
	if err != nil {
		logger.Error(action, logger.Fail, "bet", bet)
		return err
	}
	if err := send_message(conn, 0x02, payload); err != nil {
		logger.Error(action, logger.Fail, "bet", bet)
		return err
	}
	logger.Info(action, logger.Success, "bet sent", bet)
	return nil
}

func serialize_bet(bet Bet) ([]byte, error) {
	logger.debug("serialize_bet", logger.InProgress, "serializing bet", bet)
	agencyIdBytes := []byte(bet.AgencyId)
	if len(agencyIdBytes) > 255 {
		return nil, fmt.Errorf("agency id too long: %d bytes", len(agencyIdBytes))
	}
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
	payload := build_bet_payload(agencyIdBytes, nameBytes, surnameBytes, dniBytes, yearBytes, month, day, betNumberBytes)

	logger.debug("serialize_bet", logger.Success, "bet serialized", bet)
	return payload, nil
}

func build_bet_payload(agencyIdBytes, nameBytes, surnameBytes, dniBytes, yearBytes []byte, month, day uint8, betNumberBytes []byte) []byte {
	var payload []byte
	payload = appendString(payload, string(agencyIdBytes))
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

func send_message(conn net.Conn, typeMessage byte, payload []byte) error {
	logger.Info("send_message", logger.InProgress, "sending message", typeMessage)
	var header [3]byte
	header[0] = typeMessage
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