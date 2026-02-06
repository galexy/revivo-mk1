.PHONY: build-emails help

# Default target
help:
	@echo "Available targets:"
	@echo "  build-emails  - Compile MJML templates to HTML"
	@echo "  help          - Show this help message"

# Compile MJML email templates to HTML
build-emails:
	@echo "Compiling MJML templates..."
	@mkdir -p src/adapters/email/templates
	npx mjml src/adapters/email/templates/verification.mjml -o src/adapters/email/templates/verification.html
	@echo "Done. Compiled templates:"
	@ls -la src/adapters/email/templates/*.html 2>/dev/null || echo "No templates compiled yet"
