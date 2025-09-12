class Trmd < Formula
  include Language::Python::Virtualenv

  desc "Translate Markdown using OpenAI"
  homepage "https://github.com/rioriost/homebrew-trmd/"
  url "https://files.pythonhosted.org/packages/13/95/7118cdc54a9d0b567e235f1a63433da817d7bc385f1e300a830c8fa0d823/trmd-0.1.18.tar.gz"
  sha256 "0b5e55232d16aa11904cf18d04d288b9df7a68da65903a855e3d0a774e03c74d"
  license "MIT"

  depends_on "python@3.13"

  def install
    virtualenv_install_with_resources
    system libexec/"bin/python", "-m", "pip", "install", "openai"
  end

  test do
    system "#{bin}/trmd", "--help"
  end
end
