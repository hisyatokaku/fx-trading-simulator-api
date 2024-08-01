package com.example.fxtrade.models;
import com.gs.fw.finder.Operation;
import java.util.*;
public class SessionList extends SessionListAbstract
{
	public SessionList()
	{
		super();
	}

	public SessionList(int initialSize)
	{
		super(initialSize);
	}

	public SessionList(Collection c)
	{
		super(c);
	}

	public SessionList(Operation operation)
	{
		super(operation);
	}
}
