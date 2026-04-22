---
name: Struts to Spring
description: Guide Struts 1.x/2.x migration to Spring Boot — component mapping, code conversion, incremental strategy
---

Help migrate a Struts application to Spring Boot/Spring MVC.

Analyze the current Struts application and provide:

1. **Struts Inventory**
   - Struts version (1.x or 2.x)
   - Number of Actions/ActionForms/JSPs/Interceptors
   - Configuration files (struts-config.xml, struts.xml, tiles.xml, validation.xml)
   - Custom components (custom interceptors, result types, type converters)
   - Dependency on Struts-specific features (ValueStack, OGNL, Tiles)

2. **Component Mapping**
   - Map each Struts component to Spring equivalent:
     - Actions → Controllers
     - ActionForms → DTOs with Bean Validation
     - Interceptors → HandlerInterceptors or Spring Security
     - Tiles → Thymeleaf Layout Dialect
     - struts-config.xml → Java annotations
   - Identify components with no direct Spring equivalent

3. **Migration Strategy**
   - Incremental vs big-bang recommendation
   - Phase plan with priorities:
     - Phase 1: Spring Boot setup + coexistence config
     - Phase 2: Migrate service layer (framework-independent)
     - Phase 3: Convert Actions → Controllers (start with simplest)
     - Phase 4: Migrate views (JSP → Thymeleaf or REST API)
     - Phase 5: Remove Struts dependencies

4. **Code Conversion Examples**
   - For each major Action in the codebase, provide:
     - Before (Struts code)
     - After (Spring code)
     - Migration notes and gotchas

5. **View Migration**
   - JSP + Struts tags → Thymeleaf
   - Or: JSP → REST API + frontend framework (React/Angular)
   - Form handling and validation conversion
   - i18n migration (MessageResources → MessageSource)

6. **Security Migration**
   - Struts security interceptors → Spring Security
   - CSRF protection upgrade
   - OGNL injection vulnerability remediation

7. **Spring Boot Project Setup**
   - pom.xml / build.gradle with required dependencies
   - Application configuration (application.yml)
   - Coexistence configuration with Struts

8. **Testing**
   - Endpoint testing (all URLs produce same behavior)
   - Form validation parity testing
   - Security testing
   - Performance comparison

Provide the migration plan with concrete code examples for the most common patterns found in the codebase.

$ARGUMENTS
