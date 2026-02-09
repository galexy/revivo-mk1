.PHONY: build-emails help

# Default target
help:
	@echo "Available targets:"
	@echo "  build-emails  - Compile MJML templates to HTML"
	@echo "  help          - Show this help message"

# Compile MJML email templates to HTML
build-emails:
	@echo "Compiling MJML templates..."
	@mkdir -p apps/api/src/adapters/email/templates
	npx mjml apps/api/src/adapters/email/templates/verification.mjml -o apps/api/src/adapters/email/templates/verification.html
	@echo "Done. Compiled templates:"
	@ls -la apps/api/src/adapters/email/templates/*.html 2>/dev/null || echo "No templates compiled yet"
