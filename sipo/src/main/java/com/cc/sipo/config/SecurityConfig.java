package com.cc.sipo.config;

import static org.springframework.security.config.Customizer.withDefaults;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.Arrays;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    private static final String[] WHITE_LIST_URLS = {
        "/api/health",
        "/swagger-ui.html",
        "/swagger-ui/**",
        "/v3/api-docs",
        "/v3/api-docs/**",
        "/swagger-resources",
        "/swagger-resources/**"
    };

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            // 1. Habilita CORS usando la configuración que definimos abajo
            .cors(withDefaults())
            
            // 2. Deshabilita CSRF porque estamos creando una API sin estado
            .csrf(AbstractHttpConfigurer::disable)
            
            // 3. Define las reglas de autorización
            .authorizeHttpRequests(req -> req
                .requestMatchers(WHITE_LIST_URLS).permitAll() // Permite acceso a la lista blanca
                .anyRequest().authenticated() // Requiere autenticación para todo lo demás
            )
            
            // 4. Configura la gestión de sesiones como SIN ESTADO (stateless)
            // Esto es crucial para APIs REST y previene la creación de cookies de sesión
            .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS));

        return http.build();
    }

    // Bean para configurar la política de CORS de la aplicación
    @Bean
    CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();
        // Permite peticiones desde el origen donde correrá Angular (y cualquier otro)
        configuration.setAllowedOrigins(Arrays.asList("*")); 
        // Permite los métodos HTTP más comunes
        configuration.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "DELETE", "OPTIONS"));
        // Permite las cabeceras más comunes
        configuration.setAllowedHeaders(Arrays.asList("Authorization", "Cache-Control", "Content-Type"));
        
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        // Aplica esta configuración a TODAS las rutas de la aplicación
        source.registerCorsConfiguration("/**", configuration);
        
        return source;
    }
}