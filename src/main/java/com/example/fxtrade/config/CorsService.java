package com.example.fxtrade.config;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Service;

@Service
public class CorsService {
    
    @Autowired
    private CorsProperties corsProperties;
    
    public HttpHeaders createCorsHeaders() {
        HttpHeaders headers = new HttpHeaders();
        
        if (corsProperties.getAllowedOrigins() != null && !corsProperties.getAllowedOrigins().isEmpty()) {
            // For simplicity, use the first allowed origin. In production, you might want to 
            // check the actual request origin against the allowed list
            headers.add("Access-Control-Allow-Origin", corsProperties.getAllowedOrigins().get(0));
        }
        
        if (corsProperties.getAllowedMethods() != null && !corsProperties.getAllowedMethods().isEmpty()) {
            headers.add("Access-Control-Allow-Methods", String.join(", ", corsProperties.getAllowedMethods()));
        }
        
        if (corsProperties.getAllowedHeaders() != null && !corsProperties.getAllowedHeaders().isEmpty()) {
            headers.add("Access-Control-Allow-Headers", String.join(", ", corsProperties.getAllowedHeaders()));
        }
        
        headers.add("Access-Control-Allow-Credentials", String.valueOf(corsProperties.isAllowCredentials()));
        headers.add("Access-Control-Max-Age", String.valueOf(corsProperties.getMaxAge()));
        
        return headers;
    }
    
    public HttpHeaders createCorsHeaders(String requestOrigin) {
        HttpHeaders headers = new HttpHeaders();
        
        // Check if the request origin is in the allowed origins list
        if (corsProperties.getAllowedOrigins() != null && 
            corsProperties.getAllowedOrigins().contains(requestOrigin)) {
            headers.add("Access-Control-Allow-Origin", requestOrigin);
        }
        
        if (corsProperties.getAllowedMethods() != null && !corsProperties.getAllowedMethods().isEmpty()) {
            headers.add("Access-Control-Allow-Methods", String.join(", ", corsProperties.getAllowedMethods()));
        }
        
        if (corsProperties.getAllowedHeaders() != null && !corsProperties.getAllowedHeaders().isEmpty()) {
            headers.add("Access-Control-Allow-Headers", String.join(", ", corsProperties.getAllowedHeaders()));
        }
        
        headers.add("Access-Control-Allow-Credentials", String.valueOf(corsProperties.isAllowCredentials()));
        headers.add("Access-Control-Max-Age", String.valueOf(corsProperties.getMaxAge()));
        
        return headers;
    }
}