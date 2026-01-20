# Contributing to FaceFusion

Thank you for your interest in contributing to FaceFusion! We welcome contributions from the community to help improve the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/facefusion.git
   cd facefusion
   ```
3. **Create a new branch** for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Guidelines

### Code Style
- Follow PEP 8 Python style guide
- Use meaningful variable and function names
- Add comments for complex logic
- Keep functions focused and modular

### Testing
- Write tests for new features
- Ensure all tests pass before submitting
- Run tests with: `python -m pytest tests/`

### Commits
- Use clear and descriptive commit messages
- Reference issues in commit messages when applicable
- Keep commits atomic and logical

### Documentation
- Update README.md if adding new features
- Document new command-line arguments
- Include usage examples when appropriate

## Language Support

### Adding a New Language

If you want to add language support to FaceFusion:

1. **Update the Language type** in `facefusion/types.py`:
   ```python
   Language = Literal['en', 'tr', 'fr', ...]  # Add your language code
   ```

2. **Add translations** in `facefusion/locales.py`:
   - Add a new language dictionary with the language code as the key
   - Translate all strings from the English dictionary
   - Maintain the same key names and structure
   - Use `{placeholder}` for dynamic values

   Example:
   ```python
   'tr': {
       'conda_not_activated': 'conda etkinleştirilmemiş',
       'python_not_supported': 'python sürümü desteklenmiyor...',
       # ... more translations
   }
   ```

3. **Test the translation**:
   - Verify the language code works in the UI
   - Check that all strings are properly translated
   - Ensure placeholders work correctly

### Language Codes

Use standard ISO 639-1 language codes:
- `en` - English
- `tr` - Turkish
- `fr` - French
- `es` - Spanish
- `de` - German
- etc.

## Submitting Changes

1. **Push your branch** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request**:
   - Provide a clear description of your changes
   - Reference any related issues
   - Include screenshots or examples if applicable
   - Ensure CI/CD checks pass

## Pull Request Guidelines

- Keep PRs focused on a single feature or fix
- Update documentation and tests
- Provide context and rationale for changes
- Be responsive to review feedback
- Rebase on master before final submission

## Code Review

- Be open to constructive feedback
- Respond promptly to review comments
- Make requested changes in new commits
- Mark conversations as resolved once addressed

## Reporting Issues

- Use the issue tracker for bugs and feature requests
- Provide detailed descriptions and reproduction steps
- Include relevant system information
- Search for existing issues first

## License

By contributing to FaceFusion, you agree that your contributions will be licensed under the same license as the project (OpenRAIL-AS).

## Questions?

If you have questions about contributing, feel free to:
- Open an issue with your question
- Join our community and ask
- Review existing documentation

Thank you for contributing to FaceFusion!
