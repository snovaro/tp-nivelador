func send_bet(conn net.Conn, bet Bet) error {
	const action = "send-bet"
	logger.Info(action, logger.InProgress, "sending bet", bet)
	typeMessage := byte(0x02)
	safe_socket.SendAll(conn, []byte{typeMessage})
	nameBytes := []byte(bet.Name)
	// Verificar si el nombre es demasiado largo para un uint8
	lengthName := uint8(len(nameBytes))
	safe_socket.SendAll(conn, []byte{lengthName})
	safe_socket.SendAll(conn, nameBytes)
	surnameBytes := []byte(bet.Surname)
	// Verificar si el apellido es demasiado largo para un uint8
	lengthSurname := uint8(len(surnameBytes))
	safe_socket.SendAll(conn, []byte{lengthSurname})
	safe_socket.SendAll(conn, surnameBytes)
	dniBytes := make([]byte, 4)
	binary.BigEndian.PutUint32(dniBytes, bet.DNI)
	safe_socket.SendAll(conn, dniBytes)
	yearBytes := make([]byte, 2)
	binary.BigEndian.PutUint16(yearBytes, bet.Year)
	safe_socket.SendAll(conn, yearBytes)
	month := uint8(bet.Month)
	safe_socket.SendAll(conn, []byte{month})
	day := uint8(bet.Day)
	safe_socket.SendAll(conn, []byte{day})
	betNumberBytes := make([]byte, 2)
	binary.BigEndian.PutUint16(betNumberBytes, bet.BetNumber)
	safe_socket.SendAll(conn, betNumberBytes)
	logger.Info(action, logger.Success, "bet sent", bet)
	return nil
}