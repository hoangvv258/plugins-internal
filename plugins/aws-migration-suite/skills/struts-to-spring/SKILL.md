---
name: struts-to-spring
description: This skill should be used when the user asks to "migrate from Struts to Spring", "convert Struts Action to Spring Controller", "replace struts.xml with Spring annotations", "migrate JSP views from Struts", "upgrade Struts application", or mentions Struts 1, Struts 2, ActionForm, ActionMapping, OGNL, or Struts-to-Spring component mapping.
version: 1.0.0
---

# Struts to Spring Migration Skill

Migrate Apache Struts (1.x/2.x) applications to Spring Boot/Spring MVC with detailed component mapping, conversion patterns, and incremental migration strategy.

## Quick Reference: Component Mapping

### Struts 1.x → Spring

| Struts 1.x | Spring | Migration Notes |
|-----------|--------|----------------|
| `Action` | `@Controller` method | One action = one controller method |
| `DispatchAction` | `@Controller` class | Multiple methods, one class |
| `ActionForm` | DTO + `@Valid` | Replace validate() with Bean Validation |
| `ActionMapping` (struts-config.xml) | `@RequestMapping` | Annotation-based routing |
| `ActionForward` | `return "viewName"` | View resolver handles mapping |
| `ActionErrors` | `BindingResult` | Spring validation framework |
| `MessageResources` | `MessageSource` | `messages.properties` compatible |
| `DynaActionForm` | DTO or `@RequestParam` | Strongly typed preferred |
| `Validator` (validation.xml) | `@NotNull`, `@Size`, etc. | JSR 380 Bean Validation |
| `Tiles` | Thymeleaf Layout Dialect | Or keep JSP temporarily |
| `web.xml` (ActionServlet) | `@SpringBootApplication` | Auto-configuration |

### Struts 2.x → Spring

| Struts 2.x | Spring | Migration Notes |
|-----------|--------|----------------|
| `Action` class | `@Controller` | No ActionSupport needed |
| `execute()` return String | `@RequestMapping` return | View name or ResponseEntity |
| `ValueStack` (OGNL) | `Model` attribute | `model.addAttribute()` |
| `struts.xml` action mapping | `@RequestMapping` | Convention > Configuration |
| `Interceptor` | `HandlerInterceptor` / `@Aspect` | Or Spring Security |
| `@Result` | `return "viewName"` | View resolver |
| `@Action` annotation | `@RequestMapping` | Path + method |
| `validate()` method | `@Valid` + `BindingResult` | Bean Validation |
| `ActionContext` | `HttpServletRequest` / `@RequestParam` | Direct injection |
| `ServletActionContext` | `HttpServletRequest` (injected) | Spring auto-injects |
| `struts.xml` constants | `application.yml` | Spring externalized config |
| `FileUploadInterceptor` | `MultipartResolver` | `@RequestParam MultipartFile` |
| `TokenInterceptor` | Spring Security CSRF | Built-in CSRF protection |

## Configuration Migration

### struts-config.xml (Struts 1) → Spring
```xml
<!-- BEFORE: struts-config.xml -->
<action-mappings>
  <action path="/user/view"
          type="com.example.ViewUserAction"
          name="userForm"
          scope="request"
          validate="false">
    <forward name="success" path="/WEB-INF/jsp/user/view.jsp"/>
    <forward name="error" path="/WEB-INF/jsp/error.jsp"/>
  </action>
</action-mappings>
```

```java
// AFTER: Spring Controller (no XML needed)
@Controller
@RequestMapping("/user")
public class UserController {
    @GetMapping("/view")
    public String viewUser(@ModelAttribute UserForm form, Model model) {
        try {
            User user = userService.findById(form.getUserId());
            model.addAttribute("user", user);
            return "user/view";  // → templates/user/view.html
        } catch (Exception e) {
            return "error";
        }
    }
}
```

### struts.xml (Struts 2) → Spring
```xml
<!-- BEFORE: struts.xml -->
<package name="user" extends="struts-default" namespace="/user">
  <action name="list" class="com.example.UserListAction">
    <result>/WEB-INF/views/user/list.jsp</result>
    <result name="error">/WEB-INF/views/error.jsp</result>
  </action>
  <action name="save" class="com.example.UserSaveAction" method="save">
    <interceptor-ref name="defaultStack"/>
    <interceptor-ref name="token"/>
    <result type="redirectAction">list</result>
    <result name="input">/WEB-INF/views/user/form.jsp</result>
  </action>
</package>
```

```java
// AFTER: Spring Controller
@Controller
@RequestMapping("/user")
public class UserController {
    @GetMapping("/list")
    public String list(Model model) {
        model.addAttribute("users", userService.findAll());
        return "user/list";
    }

    @PostMapping("/save")
    public String save(@Valid @ModelAttribute UserDto dto, BindingResult result) {
        if (result.hasErrors()) return "user/form";
        userService.save(dto);
        return "redirect:/user/list";
    }
}
```

## View Migration: JSP → Thymeleaf

```jsp
<%-- BEFORE: Struts JSP with tags --%>
<%@ taglib prefix="s" uri="/struts-tags" %>
<s:form action="save">
  <s:textfield name="name" label="Name"/>
  <s:textarea name="description" label="Description"/>
  <s:select name="category" list="categories" listKey="id" listValue="name"/>
  <s:submit value="Save"/>
</s:form>
<s:iterator value="users">
  <tr>
    <td><s:property value="name"/></td>
    <td><s:property value="email"/></td>
  </tr>
</s:iterator>
```

```html
<!-- AFTER: Thymeleaf -->
<form th:action="@{/user/save}" th:object="${userDto}" method="post">
  <input type="text" th:field="*{name}" placeholder="Name"/>
  <textarea th:field="*{description}"></textarea>
  <select th:field="*{category}">
    <option th:each="cat : ${categories}" th:value="${cat.id}" th:text="${cat.name}"/>
  </select>
  <button type="submit">Save</button>
</form>
<tr th:each="user : ${users}">
  <td th:text="${user.name}"/>
  <td th:text="${user.email}"/>
</tr>
```

## Security Migration

### Struts Security → Spring Security
```java
// BEFORE: Custom Struts interceptor for auth
// AFTER: Spring Security configuration
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/public/**").permitAll()
                .requestMatchers("/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            )
            .formLogin(form -> form.loginPage("/login").permitAll())
            .csrf(Customizer.withDefaults())
            .build();
    }
}
```

## Incremental Migration Setup

### Spring Boot + Struts Coexistence
```java
// Spring Boot app that also serves Struts
@SpringBootApplication
public class Application extends SpringBootServletInitializer {
    @Override
    protected SpringApplicationBuilder configure(SpringApplicationBuilder builder) {
        return builder.sources(Application.class);
    }
}
```

```xml
<!-- web.xml: Route traffic to both frameworks -->
<!-- Struts handles /struts/* -->
<!-- Spring handles everything else -->
<servlet-mapping>
    <servlet-name>action</servlet-name>
    <url-pattern>/struts/*</url-pattern>
</servlet-mapping>
<servlet-mapping>
    <servlet-name>dispatcherServlet</servlet-name>
    <url-pattern>/</url-pattern>
</servlet-mapping>
```

## Migration Checklist

- [ ] Set up Spring Boot project alongside Struts
- [ ] Configure shared session/authentication
- [ ] Migrate service layer (should be framework-independent)
- [ ] Convert Actions → Controllers (one at a time)
- [ ] Convert ActionForms → DTOs with Bean Validation
- [ ] Migrate Interceptors → Spring equivalents
- [ ] Convert JSP views → Thymeleaf (or REST API)
- [ ] Migrate i18n (MessageResources → MessageSource)
- [ ] Replace Tiles → Thymeleaf Layout Dialect
- [ ] Remove struts-config.xml / struts.xml
- [ ] Remove Struts dependencies from pom.xml
- [ ] Integration test all endpoints
- [ ] Performance comparison (before vs after)
