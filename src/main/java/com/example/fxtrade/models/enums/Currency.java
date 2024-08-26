package com.example.fxtrade.models.enums;

import org.eclipse.collections.api.factory.Sets;
import org.eclipse.collections.impl.utility.ArrayIterate;

import java.util.Set;

public enum Currency {
    USD, EUR, JPY, AUD, HKD;
    public static final Set<String> CURRENCIES_AS_STRING = ArrayIterate.collect(Currency.values(), Currency::name, Sets.mutable.empty());
}
