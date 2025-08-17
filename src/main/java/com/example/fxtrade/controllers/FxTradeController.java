package com.example.fxtrade.controllers;

import com.example.fxtrade.api.request.NextRequest;
import com.example.fxtrade.api.response.NextResponse;
import com.example.fxtrade.api.response.ScenarioResponse;
import com.example.fxtrade.api.response.SessionDetailResponse;
import com.example.fxtrade.api.response.SessionResponse;
import com.example.fxtrade.component.SessionService;
import com.example.fxtrade.config.CorsService;
import com.example.fxtrade.models.GameConfig;
import com.example.fxtrade.models.Session;
import com.example.fxtrade.models.SessionList;
import org.eclipse.collections.impl.utility.ArrayIterate;
import org.eclipse.collections.impl.utility.Iterate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import jakarta.servlet.http.HttpServletRequest;
import java.util.Comparator;
import java.util.List;

@RestController
@RequestMapping(value = {"api/trade"})
public class FxTradeController {
    private final SessionService sessionService;
    private final CorsService corsService;

    @Autowired
    public FxTradeController(SessionService sessionService, CorsService corsService) {
        this.sessionService = sessionService;
        this.corsService = corsService;
    }

    @PostMapping("/start/{scenario}/{userId}")
    public NextResponse startWithUserId(@PathVariable("scenario") String scenario, @PathVariable("userId") String userId) {
        return runStart(userId, scenario);
    }

    private NextResponse runStart(String userId, String scenario) {
        Session session = sessionService.generateSession(userId, scenario);
        return NextResponse.newWith(session);
    }

    @PostMapping("/next")
    public NextResponse next(@RequestBody NextRequest nextRequest) {
        Session session = sessionService.next(nextRequest); // validation with user id and process id
        return NextResponse.newWith(session);
    }

    @GetMapping("session/sessionId/{sessionId}")
    public ResponseEntity<SessionDetailResponse> getSessionInfo(@PathVariable int sessionId, 
                                                               HttpServletRequest request) {
        Session session = sessionService.getSession(sessionId);
        SessionDetailResponse result = SessionDetailResponse.newWith(session);
        
        String origin = request.getHeader("Origin");
        HttpHeaders headers = corsService.createCorsHeaders(origin);
        
        return ResponseEntity.ok().headers(headers).body(result);
    }

    @GetMapping("sessions/userId/{userId}")
    public ResponseEntity<List<SessionResponse>> getSessionsInfo(@PathVariable("userId") String userId,
                                                                HttpServletRequest request) {
        SessionList sessions = sessionService.getSessions(userId);
        List<SessionResponse> result = Iterate.toSortedList(sessions, Comparator.comparingInt(Session::getId).reversed())
                .take(100).collect(SessionResponse::newWith);
        
        String origin = request.getHeader("Origin");
        HttpHeaders headers = corsService.createCorsHeaders(origin);
        
        return ResponseEntity.ok().headers(headers).body(result);
    }
    
    @RequestMapping(value = "sessions/userId/{userId}", method = RequestMethod.OPTIONS)
    public ResponseEntity<?> handleOptionsRequest(@PathVariable("userId") String userId,
                                                 HttpServletRequest request) {
        String origin = request.getHeader("Origin");
        HttpHeaders headers = corsService.createCorsHeaders(origin);
        
        return ResponseEntity.ok().headers(headers).build();
    }

    @GetMapping("scenarios")
    public List<String> getScenarios() {
        return ArrayIterate.collect(GameConfig.values(), GameConfig::name);
    }

    @GetMapping("scenario/{scenario}")
    public ResponseEntity<ScenarioResponse> getScenarios(@PathVariable("scenario") String scenario,
                                                        HttpServletRequest request) {
        ScenarioResponse result = new ScenarioResponse(GameConfig.valueOf(scenario));
        
        String origin = request.getHeader("Origin");
        HttpHeaders headers = corsService.createCorsHeaders(origin);
        
        return ResponseEntity.ok().headers(headers).body(result);
    }
    
    @RequestMapping(value = "session/sessionId/{sessionId}", method = RequestMethod.OPTIONS)
    public ResponseEntity<?> handleSessionOptionsRequest(@PathVariable int sessionId,
                                                       HttpServletRequest request) {
        String origin = request.getHeader("Origin");
        HttpHeaders headers = corsService.createCorsHeaders(origin);
        
        return ResponseEntity.ok().headers(headers).build();
    }
    
    @RequestMapping(value = "scenario/{scenario}", method = RequestMethod.OPTIONS)
    public ResponseEntity<?> handleScenarioOptionsRequest(@PathVariable String scenario,
                                                        HttpServletRequest request) {
        String origin = request.getHeader("Origin");
        HttpHeaders headers = corsService.createCorsHeaders(origin);
        
        return ResponseEntity.ok().headers(headers).build();
    }
}
