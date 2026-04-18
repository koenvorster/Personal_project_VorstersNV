package dev.koenvorsters.lead.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record LeadRequest(
        @NotBlank(message = "Naam is verplicht")
        @Size(max = 200)
        String naam,

        @NotBlank(message = "E-mail is verplicht")
        @Email(message = "Ongeldig e-mailadres")
        @Size(max = 254)
        String email,

        @Size(max = 200)
        String bedrijf,

        @Size(max = 100)
        String dienst,

        @NotBlank(message = "Bericht is verplicht")
        @Size(min = 10, max = 5000, message = "Bericht moet minimaal 10 tekens bevatten")
        String bericht
) {}
