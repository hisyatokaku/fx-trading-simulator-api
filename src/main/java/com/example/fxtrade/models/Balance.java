package com.example.fxtrade.models;
import com.example.fxtrade.models.enums.Currency;

import java.util.Date;

public class Balance extends BalanceAbstract
{
	public Balance()
	{
		super();
		// You must not modify this constructor. Mithra calls this internally.
		// You can call this constructor. You can also add new constructors.
	}

	public Balance(int sessionId, Date date, String currency, double amount)
	{
		this();
		this.setSessionId(sessionId);
		this.setDate(date);
		this.setCurrency(currency);
		this.setAmount(amount);
	}
}
