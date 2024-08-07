package com.example.fxtrade.models;
import java.sql.Timestamp;
public class Trader extends TraderAbstract
{
	public Trader(String userId, String type)
	{
		super();
		this.setUserId(userId);
		this.setType(type);
	}

	public Trader()
	{
		super();
		// You must not modify this constructor. Mithra calls this internally.
		// You can call this constructor. You can also add new constructors.
	}
}
