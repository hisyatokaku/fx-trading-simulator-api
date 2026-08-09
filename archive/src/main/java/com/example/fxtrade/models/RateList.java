package com.example.fxtrade.models;
import com.gs.fw.finder.Operation;
import java.util.*;
public class RateList extends RateListAbstract
{
	public RateList()
	{
		super();
	}

	public RateList(int initialSize)
	{
		super(initialSize);
	}

	public RateList(Collection c)
	{
		super(c);
	}

	public RateList(Operation operation)
	{
		super(operation);
	}
}
