package com.example.fxtrade.controllers;

import com.example.fxtrade.api.request.NextRequest;
import com.example.fxtrade.api.response.NextResponse;
import com.example.fxtrade.api.response.SessionResponse;
import com.example.fxtrade.component.SessionService;
import com.example.fxtrade.models.Session;
import com.example.fxtrade.models.SessionList;
import org.eclipse.collections.api.factory.Lists;
import org.eclipse.collections.impl.utility.Iterate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Optional;

@RestController
@RequestMapping(value = {"api/trade"})
public class FxTradeController {
    private final SessionService sessionService;

    @Autowired
    public FxTradeController(SessionService sessionService) {
        this.sessionService = sessionService;
    }
    @PostMapping("/start/{scenario}/{userId}")
    public NextResponse startWithUserId(@PathVariable("scenario") String scenario, @PathVariable("userId") String userId) {
        return runStart(Optional.of(userId), scenario);
    }

    private NextResponse runStart(Optional<String> userId, String scenario)
    {
        Session session = sessionService.generateSession(userId, scenario);
        return NextResponse.newWith(session);
    }

    @PostMapping("/next")
    public NextResponse next(@RequestBody NextRequest nextRequest) {
        Session session = sessionService.next(nextRequest); // validation with user id and process id
        return NextResponse.newWith(session);
    }

    @GetMapping("session/sessionId/{sessionId}")
    public SessionResponse getSessionInfo(@PathVariable int sessionId) {
        Session session = sessionService.getSession(sessionId);
        return SessionResponse.newWith(session);
    }

    @GetMapping("sessions/userId/{userId}")
    public List<Integer> getSessionsInfo(@PathVariable("userId") String userId) {
        SessionList sessions = sessionService.getSessions(userId);
        return Iterate.collect(sessions, Session::getId, Lists.mutable.empty());
    }
}
