package com.example.fxtrade.controllers;

import com.example.fxtrade.config.CorsService;
import com.example.fxtrade.models.RateMatrix;
import com.example.fxtrade.utils.reladomo.DateUtil;
import org.eclipse.collections.api.factory.Maps;
import org.eclipse.collections.api.tuple.Twin;
import org.eclipse.collections.impl.utility.Iterate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import jakarta.servlet.http.HttpServletRequest;
import java.time.LocalDate;
import java.util.Map;
import java.util.Set;

@RestController
@RequestMapping(value = {"api/rate"})
public class RateController {
    
    @Autowired
    private CorsService corsService;

    @GetMapping("{date}")
    public ResponseEntity<Map<String, Double>> getRate(@PathVariable @DateTimeFormat(pattern = "yyyy-MM-dd") LocalDate date,
                                                       HttpServletRequest request) {
        Map<String, Double> currencyPairToRate = Maps.mutable.empty();
        
        try {
            RateMatrix rateMatrix = RateMatrix.newWith(DateUtil.toDate(date));
            Set<Twin<String>> currencyFromAndTos = rateMatrix.getCurrencyFromAndTo();
            
            if (currencyFromAndTos.isEmpty()) {
                // Return error response for dates with no data
                currencyPairToRate.put("error", -1.0);
                currencyPairToRate.put("message", Double.valueOf("No rate data available for " + date + ". Available range: 2002-04-01 to 2023-06-13".hashCode()));
            } else {
                Iterate.forEach(currencyFromAndTos, currencyFromAndTo -> {
                    String currencyFrom = currencyFromAndTo.getOne();
                    String currencyTo = currencyFromAndTo.getTwo();
                    double rate = rateMatrix.getRate(currencyFrom, currencyTo);
                    currencyPairToRate.put(currencyFrom + "/" + currencyTo, rate);
                });
            }
        } catch (Exception e) {
            // Handle any unexpected errors
            currencyPairToRate.put("error", -1.0);
            currencyPairToRate.put("message", Double.valueOf("No rate data available for " + date + ". Available range: 2002-04-01 to 2023-06-13".hashCode()));
        }
        
        String origin = request.getHeader("Origin");
        HttpHeaders headers = corsService.createCorsHeaders(origin);
        
        return ResponseEntity.ok().headers(headers).body(currencyPairToRate);
    }
    
    @RequestMapping(value = "{date}", method = RequestMethod.OPTIONS)
    public ResponseEntity<?> handleRateOptionsRequest(@PathVariable String date,
                                                      HttpServletRequest request) {
        String origin = request.getHeader("Origin");
        HttpHeaders headers = corsService.createCorsHeaders(origin);
        
        return ResponseEntity.ok().headers(headers).build();
    }
}
