(async(root) => {
  if (await root.getUser()) {
    const article = document.getElementsByTagName('article')[0];
    if (article) {
      while(article.firstChild) {
        article.removeChild(article.firstChild);
      }
      const strong = document.createElement('strong');
      strong.innerText = "Welcome back, you are already logged in";
      article.appendChild(strong);
    }
    return;
  }
  const login = async () =>  {
    const password = (document.getElementById('password') as HTMLInputElement|null)?.value
    const userid = (document.getElementById('userid') as HTMLInputElement|null)?.value
    if (password && userid) {
      const login = await root.getFromAPI(`login`, 'POST', {
          user_id: userid,
          password,
        }, 10000) as {success?:boolean};
      if (!login?.success) {
        await root.alert("Login failed!");
        window.location.reload()
        return;
      }
      window.location.reload();
    }
  }
  document.getElementById('login')?.addEventListener('click', login)
  document.getElementById('login')?.addEventListener('keyup', (event: KeyboardEvent) => {
    if (event.key === 'Enter') {
      login();
    }
  })
  document.getElementById('password')?.addEventListener('keyup', (event: KeyboardEvent) => {
    if (event.key === 'Enter') {
      login();
    }
  })
  document.getElementById('userid')?.addEventListener('keyup', (event: KeyboardEvent) => {
    if (event.key === 'Enter') {
      login();
    }
  })
})(window.bjoernbuettner);
