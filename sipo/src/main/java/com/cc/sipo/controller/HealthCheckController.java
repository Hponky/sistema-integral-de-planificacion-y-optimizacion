package com.cc.sipo.controller;

import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/health") // Todas las rutas en este controlador empezarán con /api/health
public class HealthCheckController {

    @GetMapping
    public Map<String, String> checkHealth() {
        // Devuelve un objeto Map, que Spring convertirá automáticamente a JSON.
        return Map.of("status", "UP");
    }
}