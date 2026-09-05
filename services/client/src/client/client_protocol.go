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
	var payload []byte
	logger.debug("serialize_bet", logger.InProgress, "serializing bet", bet)
	agencyIdBytes := []byte(bet.AgencyId)
	if len(agencyIdBytes) > 255 {
		return nil, fmt.Errorf("agency id too long: %d bytes", len(agencyIdBytes))
	}
	lengthAgencyId := uint8(len(agencyIdBytes))
	payload = append(payload, lengthAgencyId)
	payload = append(payload, agencyIdBytes...)
	nameBytes := []byte(bet.Name)
	if len(nameBytes) > 255 {
		return nil, fmt.Errorf("name too long: %d bytes", len(nameBytes))
	}
	lengthName := uint8(len(nameBytes))
	payload = append(payload, lengthName)
	payload = append(payload, nameBytes...)
	surnameBytes := []byte(bet.Surname)
	if len(surnameBytes) > 255 {
		return nil, fmt.Errorf("surname too long: %d bytes", len(surnameBytes))
	}
	lengthSurname := uint8(len(surnameBytes))
	payload = append(payload, lengthSurname)
	payload = append(payload, surnameBytes...)
	dniBytes := make([]byte, 4)
	binary.BigEndian.PutUint32(dniBytes, bet.DNI)
	payload = append(payload, dniBytes...)
	yearBytes := make([]byte, 2)
	binary.BigEndian.PutUint16(yearBytes, bet.Year)
	payload = append(payload, yearBytes...)
	month := uint8(bet.Month)
	payload = append(payload, month)
	day := uint8(bet.Day)
	payload = append(payload, day)
	betNumberBytes := make([]byte, 2)
	binary.BigEndian.PutUint16(betNumberBytes, bet.BetNumber)
	payload = append(payload, betNumberBytes...)
	logger.debug("serialize_bet", logger.Success, "bet serialized", bet)
	return payload, nil
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