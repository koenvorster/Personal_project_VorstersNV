package dev.koenvorsters.lead.dto;

import dev.koenvorsters.lead.Lead;
import java.time.OffsetDateTime;

public record LeadResponse(
        Long id,
        String naam,
        String email,
        String bedrijf,
        String dienst,
        String status,
        OffsetDateTime aangemaaktOp
) {
    public static LeadResponse from(Lead lead) {
        return new LeadResponse(
                lead.getId(),
                lead.getNaam(),
                lead.getEmail(),
                lead.getBedrijf(),
                lead.getDienst(),
                lead.getStatus(),
                lead.getAangemaaktOp()
        );
    }
}
