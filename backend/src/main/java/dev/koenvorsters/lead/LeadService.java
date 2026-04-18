package dev.koenvorsters.lead;

import dev.koenvorsters.lead.dto.LeadRequest;
import dev.koenvorsters.lead.dto.LeadResponse;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
public class LeadService {

    private final LeadRepository repository;

    public LeadService(LeadRepository repository) {
        this.repository = repository;
    }

    public LeadResponse save(LeadRequest request) {
        Lead lead = new Lead();
        lead.setNaam(request.naam());
        lead.setEmail(request.email());
        lead.setBedrijf(request.bedrijf());
        lead.setDienst(request.dienst());
        lead.setBericht(request.bericht());
        return LeadResponse.from(repository.save(lead));
    }

    public List<LeadResponse> findAll() {
        return repository.findAllByOrderByAangemaaktOpDesc()
                .stream()
                .map(LeadResponse::from)
                .toList();
    }
}
