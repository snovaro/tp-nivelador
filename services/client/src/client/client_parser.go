func parse_bet(betString string, agencyId string) (Bet, error) {
	parts := strings.Split(betString, ",")
	if len(parts) != 5 {
		return Bet{}, fmt.Errorf("invalid bet format: %s", betString)
	}

	name := parts[0]
	surname := parts[1]

	dni, err := strconv.ParseUint(parts[2], 10, 32)
	if err != nil {
		return Bet{}, fmt.Errorf("invalid DNI: %s", parts[2])
	}

	dateParts := strings.Split(parts[3], "-")
	if len(dateParts) != 3 {
		return Bet{}, fmt.Errorf("invalid date format: %s", parts[3])
	}

	year, err := strconv.ParseUint(dateParts[0], 10, 16)
	if err != nil {
		return Bet{}, fmt.Errorf("invalid year: %s", dateParts[0])
	}

	month, err := strconv.ParseUint(dateParts[1], 10, 8)
	if err != nil {
		return Bet{}, fmt.Errorf("invalid month: %s", dateParts[1])
	}

	day, err := strconv.ParseUint(dateParts[2], 10, 8)
	if err != nil {
		return Bet{}, fmt.Errorf("invalid day: %s", dateParts[2])
	}

	betNumber, err := strconv.ParseUint(parts[4], 10, 16)
	if err != nil {
		return Bet{}, fmt.Errorf("invalid bet number: %s", parts[4])
	}

	return Bet{
		AgencyId:   agencyId,
		Name:       name,
		Surname:    surname,
		DNI:        uint32(dni),
		Year:       uint16(year),
		Month:      uint8(month),
		Day:        uint8(day),
		BetNumber:  uint16(betNumber),
	}, nil
}