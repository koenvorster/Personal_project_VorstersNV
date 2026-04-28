"""
Bootstrap script – maakt de volledige Spring Boot backend-structuur aan.
Gebruik: python setup_backend.py
"""
import os
import textwrap

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(ROOT, "backend")

FILES: dict[str, str] = {}

# ── pom.xml ────────────────────────────────────────────────────────────────────
FILES["pom.xml"] = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <project xmlns="http://maven.apache.org/POM/4.0.0"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
        <modelVersion>4.0.0</modelVersion>

        <parent>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-parent</artifactId>
            <version>3.3.5</version>
            <relativePath/>
        </parent>

        <groupId>dev.koenvorsters</groupId>
        <artifactId>api</artifactId>
        <version>0.0.1-SNAPSHOT</version>
        <name>koenvorsters-api</name>
        <description>Koen Vorsters Freelance IT – Spring Boot API</description>

        <properties>
            <java.version>21</java.version>
        </properties>

        <dependencies>
            <dependency>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-starter-web</artifactId>
            </dependency>
            <dependency>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-starter-data-jpa</artifactId>
            </dependency>
            <dependency>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-starter-validation</artifactId>
            </dependency>
            <dependency>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-starter-actuator</artifactId>
            </dependency>
            <dependency>
                <groupId>org.postgresql</groupId>
                <artifactId>postgresql</artifactId>
                <scope>runtime</scope>
            </dependency>
            <dependency>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-starter-test</artifactId>
                <scope>test</scope>
            </dependency>
            <dependency>
                <groupId>com.h2database</groupId>
                <artifactId>h2</artifactId>
                <scope>test</scope>
            </dependency>
        </dependencies>

        <build>
            <plugins>
                <plugin>
                    <groupId>org.springframework.boot</groupId>
                    <artifactId>spring-boot-maven-plugin</artifactId>
                </plugin>
            </plugins>
        </build>
    </project>
    """)

# ── Dockerfile ─────────────────────────────────────────────────────────────────
FILES["Dockerfile"] = textwrap.dedent("""\
    # Stage 1 – build
    FROM maven:3.9.9-eclipse-temurin-21 AS build
    WORKDIR /app
    COPY pom.xml .
    RUN mvn dependency:go-offline -q
    COPY src ./src
    RUN mvn package -DskipTests -q

    # Stage 2 – runtime
    FROM eclipse-temurin:21-jre-alpine
    WORKDIR /app
    COPY --from=build /app/target/*.jar app.jar
    EXPOSE 8080
    ENTRYPOINT ["java", "-jar", "app.jar"]
    """)

# ── application.properties ─────────────────────────────────────────────────────
FILES["src/main/resources/application.properties"] = textwrap.dedent("""\
    spring.application.name=koenvorsters-api

    # Database (lokale dev)
    spring.datasource.url=jdbc:postgresql://localhost:5432/vorstersNV
    spring.datasource.username=vorstersNV
    spring.datasource.password=dev-password-change-me
    spring.datasource.driver-class-name=org.postgresql.Driver

    # JPA / Hibernate – ddl-auto=update maakt leads-tabel automatisch aan
    spring.jpa.hibernate.ddl-auto=update
    spring.jpa.properties.hibernate.dialect=org.hibernate.dialect.PostgreSQLDialect
    spring.jpa.show-sql=false

    # Server
    server.port=8080

    # Actuator
    management.endpoints.web.exposure.include=health
    management.endpoint.health.show-details=never
    """)

# ── application-docker.properties ─────────────────────────────────────────────
FILES["src/main/resources/application-docker.properties"] = textwrap.dedent("""\
    # Override voor Docker Compose – database hostname via service-naam
    spring.datasource.url=jdbc:postgresql://database:5432/vorstersNV
    spring.datasource.password=${DB_PASSWORD:dev-password-change-me}
    """)

# ── Main application class ─────────────────────────────────────────────────────
FILES["src/main/java/dev/koenvorsters/KoenVorstersApiApplication.java"] = textwrap.dedent("""\
    package dev.koenvorsters;

    import org.springframework.boot.SpringApplication;
    import org.springframework.boot.autoconfigure.SpringBootApplication;

    @SpringBootApplication
    public class KoenVorstersApiApplication {

        public static void main(String[] args) {
            SpringApplication.run(KoenVorstersApiApplication.class, args);
        }
    }
    """)

# ── CORS configuratie ──────────────────────────────────────────────────────────
FILES["src/main/java/dev/koenvorsters/config/CorsConfig.java"] = textwrap.dedent("""\
    package dev.koenvorsters.config;

    import org.springframework.context.annotation.Bean;
    import org.springframework.context.annotation.Configuration;
    import org.springframework.web.servlet.config.annotation.CorsRegistry;
    import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

    @Configuration
    public class CorsConfig {

        @Bean
        public WebMvcConfigurer corsConfigurer() {
            return new WebMvcConfigurer() {
                @Override
                public void addCorsMappings(CorsRegistry registry) {
                    registry.addMapping("/api/**")
                            .allowedOrigins(
                                    "http://localhost:3000",
                                    "https://koenvorsters.dev"
                            )
                            .allowedMethods("GET", "POST", "PATCH", "OPTIONS")
                            .allowedHeaders("*");
                }
            };
        }
    }
    """)

# ── Lead entity ────────────────────────────────────────────────────────────────
FILES["src/main/java/dev/koenvorsters/lead/Lead.java"] = textwrap.dedent("""\
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
    """)

# ── LeadRepository ─────────────────────────────────────────────────────────────
FILES["src/main/java/dev/koenvorsters/lead/LeadRepository.java"] = textwrap.dedent("""\
    package dev.koenvorsters.lead;

    import org.springframework.data.jpa.repository.JpaRepository;
    import org.springframework.stereotype.Repository;
    import java.util.List;

    @Repository
    public interface LeadRepository extends JpaRepository<Lead, Long> {
        List<Lead> findAllByOrderByAangemaaktOpDesc();
    }
    """)

# ── LeadRequest DTO ────────────────────────────────────────────────────────────
FILES["src/main/java/dev/koenvorsters/lead/dto/LeadRequest.java"] = textwrap.dedent("""\
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
    """)

# ── LeadResponse DTO ───────────────────────────────────────────────────────────
FILES["src/main/java/dev/koenvorsters/lead/dto/LeadResponse.java"] = textwrap.dedent("""\
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
    """)

# ── LeadService ────────────────────────────────────────────────────────────────
FILES["src/main/java/dev/koenvorsters/lead/LeadService.java"] = textwrap.dedent("""\
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
    """)

# ── LeadController ─────────────────────────────────────────────────────────────
FILES["src/main/java/dev/koenvorsters/lead/LeadController.java"] = textwrap.dedent("""\
    package dev.koenvorsters.lead;

    import dev.koenvorsters.lead.dto.LeadRequest;
    import dev.koenvorsters.lead.dto.LeadResponse;
    import jakarta.validation.Valid;
    import org.springframework.http.HttpStatus;
    import org.springframework.http.ResponseEntity;
    import org.springframework.web.bind.annotation.*;
    import java.util.List;

    @RestController
    @RequestMapping("/api/leads")
    public class LeadController {

        private final LeadService service;

        public LeadController(LeadService service) {
            this.service = service;
        }

        @PostMapping
        public ResponseEntity<LeadResponse> create(@Valid @RequestBody LeadRequest request) {
            return ResponseEntity.status(HttpStatus.CREATED).body(service.save(request));
        }

        @GetMapping
        public List<LeadResponse> list() {
            return service.findAll();
        }
    }
    """)

# ── Test placeholder ───────────────────────────────────────────────────────────
FILES["src/test/java/dev/koenvorsters/KoenVorstersApiApplicationTests.java"] = textwrap.dedent("""\
    package dev.koenvorsters;

    import org.junit.jupiter.api.Test;
    import org.springframework.boot.test.context.SpringBootTest;
    import org.springframework.test.context.ActiveProfiles;

    @SpringBootTest
    @ActiveProfiles("test")
    class KoenVorstersApiApplicationTests {

        @Test
        void contextLoads() {
        }
    }
    """)

# ── test application.properties ────────────────────────────────────────────────
FILES["src/test/resources/application.properties"] = textwrap.dedent("""\
    spring.datasource.url=jdbc:h2:mem:testdb
    spring.datasource.driver-class-name=org.h2.Driver
    spring.datasource.username=sa
    spring.datasource.password=
    spring.jpa.hibernate.ddl-auto=create-drop
    spring.jpa.database-platform=org.hibernate.dialect.H2Dialect
    """)


# ── Frontend – contact pagina ──────────────────────────────────────────────────
EXTRA_FILES: dict[str, str] = {}

EXTRA_FILES["frontend/app/contact/page.tsx"] = textwrap.dedent("""\
    'use client'

    import { useState } from 'react'
    import { motion } from 'framer-motion'
    import { Mail, Send, CheckCircle, AlertCircle } from 'lucide-react'
    import GlassCard from '@/components/ui/GlassCard'
    import GradientButton from '@/components/ui/GradientButton'

    const DIENSTEN = [
      { value: '', label: 'Kies een dienst...' },
      { value: 'full-stack', label: 'Full-Stack Development' },
      { value: 'ai-ml', label: 'AI / Machine Learning' },
      { value: 'iot', label: 'IoT & Embedded' },
      { value: 'consulting', label: 'IT Consulting' },
    ]

    export default function ContactPage() {
      const [form, setForm] = useState({ naam: '', email: '', bedrijf: '', dienst: '', bericht: '' })
      const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
      const [errorMsg, setErrorMsg] = useState('')

      const handleChange = (
        e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
      ) => setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }))

      const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setStatus('loading')
        try {
          const res = await fetch('http://localhost:8081/api/leads', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(form),
          })
          if (!res.ok) {
            const data = await res.json().catch(() => ({}))
            throw new Error(data?.message || `HTTP ${res.status}`)
          }
          setStatus('success')
        } catch (err) {
          setErrorMsg(err instanceof Error ? err.message : 'Iets ging mis.')
          setStatus('error')
        }
      }

      if (status === 'success') {
        return (
          <main className="min-h-screen bg-slate-950 flex items-center justify-center px-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
              className="text-center max-w-md"
            >
              <div className="flex justify-center mb-6">
                <div className="p-4 rounded-full bg-green-500/20">
                  <CheckCircle className="w-12 h-12 text-green-400" />
                </div>
              </div>
              <h2 className="text-3xl font-bold text-white mb-3">Bericht verzonden!</h2>
              <p className="text-slate-400">
                Bedankt voor je bericht. Ik neem zo snel mogelijk contact met je op.
              </p>
            </motion.div>
          </main>
        )
      }

      return (
        <main className="min-h-screen bg-slate-950 py-20 px-4">
          <div className="max-w-2xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="text-center mb-12"
            >
              <div className="flex justify-center mb-4">
                <div className="p-3 rounded-2xl bg-green-500/20">
                  <Mail className="w-8 h-8 text-green-400" />
                </div>
              </div>
              <h1 className="text-4xl sm:text-5xl font-extrabold text-white mb-4">
                Neem{' '}
                <span className="bg-gradient-to-r from-green-400 to-emerald-500 bg-clip-text text-transparent">
                  contact
                </span>{' '}
                op
              </h1>
              <p className="text-slate-400 text-lg">
                Heb je een project in gedachten? Laat het me weten en ik kom zo snel mogelijk bij je terug.
              </p>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
            >
              <GlassCard className="p-8">
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-1.5">
                        Naam <span className="text-red-400">*</span>
                      </label>
                      <input
                        type="text"
                        name="naam"
                        value={form.naam}
                        onChange={handleChange}
                        required
                        placeholder="Jan Janssen"
                        className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500/50 transition-all"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-1.5">
                        E-mail <span className="text-red-400">*</span>
                      </label>
                      <input
                        type="email"
                        name="email"
                        value={form.email}
                        onChange={handleChange}
                        required
                        placeholder="jan@bedrijf.be"
                        className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500/50 transition-all"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-1.5">
                        Bedrijf <span className="text-slate-500 text-xs">(optioneel)</span>
                      </label>
                      <input
                        type="text"
                        name="bedrijf"
                        value={form.bedrijf}
                        onChange={handleChange}
                        placeholder="Mijn Bedrijf NV"
                        className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500/50 transition-all"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-1.5">
                        Dienst
                      </label>
                      <select
                        name="dienst"
                        value={form.dienst}
                        onChange={handleChange}
                        className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-white/10 text-white focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500/50 transition-all"
                      >
                        {DIENSTEN.map((d) => (
                          <option key={d.value} value={d.value} className="bg-slate-900">
                            {d.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1.5">
                      Bericht <span className="text-red-400">*</span>
                    </label>
                    <textarea
                      name="bericht"
                      value={form.bericht}
                      onChange={handleChange}
                      required
                      minLength={10}
                      rows={5}
                      placeholder="Vertel me over je project of vraag..."
                      className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500/50 transition-all resize-none"
                    />
                  </div>
                  {status === 'error' && (
                    <div className="flex items-center gap-2 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                      <AlertCircle className="w-4 h-4 flex-shrink-0" />
                      {errorMsg}
                    </div>
                  )}
                  <GradientButton
                    type="submit"
                    variant="primary"
                    disabled={status === 'loading'}
                    className="w-full text-base py-4 flex items-center justify-center gap-2"
                  >
                    {status === 'loading' ? (
                      <>
                        <span className="animate-spin rounded-full h-4 w-4 border-2 border-white/30 border-t-white" />
                        Verzenden...
                      </>
                    ) : (
                      <>
                        Verstuur bericht <Send className="w-4 h-4" />
                      </>
                    )}
                  </GradientButton>
                </form>
              </GlassCard>
            </motion.div>
          </div>
        </main>
      )
    }
    """)


def write_file(rel_path: str, content: str, base: str = BASE) -> None:
    full_path = os.path.join(base, rel_path.replace("/", os.sep))
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"  ✅ {rel_path}")


if __name__ == "__main__":
    print(f"\n🚀 Spring Boot backend aanmaken in: {BASE}\n")
    for path, content in FILES.items():
        write_file(path, content)
    print(f"\n📦 Frontend bestanden aanmaken...\n")
    for path, content in EXTRA_FILES.items():
        write_file(path, content, base=ROOT)
    total = len(FILES) + len(EXTRA_FILES)
    print(f"\n✅ Klaar! {total} bestanden aangemaakt.")
    print("\nVolgende stap:")
    print("  cd backend && mvn package -DskipTests  ← optioneel lokaal testen")
    print("  docker compose up -d  ← start alles via Docker")
