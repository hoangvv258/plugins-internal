---
name: java-modernization
description: This skill should be used when the user asks to "modernize a Java application", "decompose a Java monolith", "migrate Java to microservices", "containerize Java app", "use strangler fig pattern", "convert Java WAR to Spring Boot", or mentions Java modernization, monolith decomposition, Domain-Driven Design for migration, or Java framework upgrades.
version: 1.0.0
---

# Java Modernization Skill

Modernize Java applications from legacy monoliths to cloud-native architectures using proven patterns and incremental strategies.

## Modernization Paths

```
Legacy Java (J2EE, Struts, EJB)
    │
    ├── Path A: Replatform (Quick)
    │   └── Containerize → ECS/EKS
    │
    ├── Path B: Refactor to Spring Boot (Medium)
    │   └── Spring Boot → ECS Fargate / Elastic Beanstalk
    │
    └── Path C: Refactor to Serverless (Full)
        └── Spring Cloud Function / Lambda Handler → API Gateway + Lambda
```

## Monolith Decomposition

### Step 1: Identify Bounded Contexts (DDD)
- Map business domains to code modules
- Identify shared data and cross-cutting concerns
- Define service boundaries along domain lines

### Step 2: Strangler Fig Pattern
```
Phase 1: Proxy → Monolith (all traffic)
Phase 2: Proxy → Monolith (existing) + New Service (new features)
Phase 3: Proxy → Monolith (shrinking) + Services (growing)
Phase N: Proxy → Microservices only → Decommission monolith
```

### Step 3: Data Decomposition
- Database-per-service (target)
- Shared database (transitional, use schema isolation)
- Event-driven sync between services (CDC, outbox pattern)

## Framework Migration Patterns

### J2EE / EJB → Spring Boot

| J2EE Component | Spring Equivalent |
|---------------|-------------------|
| EJB Stateless | `@Service` |
| EJB Stateful | `@Scope("session")` + `@Service` |
| EJB Entity | JPA `@Entity` |
| JMS MDB | `@JmsListener` |
| JNDI Lookup | `@Autowired` (DI) |
| Servlet | `@RestController` |
| JSP | Thymeleaf / REST API + SPA |
| EAR/WAR | Executable JAR (`spring-boot-maven-plugin`) |
| application.xml | `application.yml` |
| Container-managed TX | `@Transactional` |

### Servlet/JSP → REST API

```java
// Before: JSP-based (server-side rendering)
@WebServlet("/users")
public class UserServlet extends HttpServlet {
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) {
        List<User> users = dao.findAll();
        req.setAttribute("users", users);
        req.getRequestDispatcher("/WEB-INF/user-list.jsp").forward(req, resp);
    }
}

// After: REST API (frontend separation)
@RestController
@RequestMapping("/api/users")
public class UserController {
    @GetMapping
    public List<UserDto> getUsers() {
        return userService.findAll().stream()
            .map(UserDto::from)
            .toList();
    }
}
```

### Database Migration Patterns

| Current | Target | Migration Path |
|---------|--------|---------------|
| Oracle | Aurora PostgreSQL | AWS SCT + DMS |
| SQL Server | Aurora PostgreSQL | AWS SCT + DMS |
| MySQL | Aurora MySQL | DMS (compatible) |
| Any RDBMS | DynamoDB | Redesign data model (denormalize) |

## Containerization

### Dockerfile for Spring Boot
```dockerfile
FROM eclipse-temurin:21-jre-alpine AS runtime
WORKDIR /app
COPY target/*.jar app.jar
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget -q --spider http://localhost:8080/actuator/health || exit 1
ENTRYPOINT ["java", "-XX:+UseContainerSupport", "-XX:MaxRAMPercentage=75.0", "-jar", "app.jar"]
```

### Multi-stage Build (with Maven)
```dockerfile
FROM eclipse-temurin:21-jdk-alpine AS build
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline
COPY src ./src
RUN mvn package -DskipTests

FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
ENTRYPOINT ["java", "-jar", "app.jar"]
```

## Java Version Upgrade Path

| From | To | Key Changes |
|------|----|-------------|
| Java 8 | Java 11 | Modules, `var`, HTTP Client, remove Java EE |
| Java 11 | Java 17 | Records, sealed classes, text blocks, pattern matching |
| Java 17 | Java 21 | Virtual threads, pattern matching, sequenced collections |

**Critical:** Remove deprecated Java EE modules before upgrading
```xml
<!-- Add if migrating from Java 8 to 11+ -->
<dependency>
    <groupId>jakarta.xml.bind</groupId>
    <artifactId>jakarta.xml.bind-api</artifactId>
</dependency>
```

## Testing Strategy for Modernization

1. **Before migration** — Create comprehensive test suite on legacy system
2. **Contract tests** — Define API contracts before splitting services
3. **Integration tests** — Test service interactions end-to-end
4. **Performance baseline** — Benchmark before and after
5. **Chaos testing** — Verify resilience of new architecture
