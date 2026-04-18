package dev.koenvorsters.lead;

import jakarta.persistence.*;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import java.time.OffsetDateTime;

@Entity
@Table(name = "leads")
public class Lead {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @NotBlank
    @Size(max = 200)
    @Column(nullable = false, length = 200)
    private String naam;

    @NotBlank
    @Email
    @Size(max = 254)
    @Column(nullable = false, length = 254)
    private String email;

    @Size(max = 200)
    @Column(length = 200)
    private String bedrijf;

    @Size(max = 100)
    @Column(length = 100)
    private String dienst;

    @NotBlank
    @Size(min = 10, max = 5000)
    @Column(nullable = false, columnDefinition = "TEXT")
    private String bericht;

    @Column(nullable = false, length = 50)
    private String status = "nieuw";

    @Column(name = "aangemaakt_op", nullable = false)
    private OffsetDateTime aangemaaktOp = OffsetDateTime.now();

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getNaam() { return naam; }
    public void setNaam(String naam) { this.naam = naam; }

    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }

    public String getBedrijf() { return bedrijf; }
    public void setBedrijf(String bedrijf) { this.bedrijf = bedrijf; }

    public String getDienst() { return dienst; }
    public void setDienst(String dienst) { this.dienst = dienst; }

    public String getBericht() { return bericht; }
    public void setBericht(String bericht) { this.bericht = bericht; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public OffsetDateTime getAangemaaktOp() { return aangemaaktOp; }
    public void setAangemaaktOp(OffsetDateTime v) { this.aangemaaktOp = v; }
}
