package com.example.fxtrade.models;
import com.gs.fw.finder.Operation;
import java.util.*;
public class TraderList extends TraderListAbstract
{
	public TraderList()
	{
		super();
	}

	public TraderList(int initialSize)
	{
		super(initialSize);
	}

	public TraderList(Collection c)
	{
		super(c);
	}

	public TraderList(Operation operation)
	{
		super(operation);
	}
}
