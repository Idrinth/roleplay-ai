(async() => {
  if (! window?.PayPal?.Donation?.Button) {
    return;
  }
  window.PayPal.Donation.Button({
    env: 'production',
    hosted_button_id: 'AENZ9E63F85G8',
    image: {
      src: 'https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif',
      alt: 'Donate with PayPal',
      title: 'PayPal - The safer, easier way to pay online!',
    }
  }).render('#donate-button');
  requestAnimationFrame(() => {
    const paypal = document.getElementById('donate-button');
    if (! paypal) {
      return;
    }
    paypal.setAttribute('tabindex', '0');
    paypal.setAttribute('role', 'button');
    paypal.setAttribute('aria-label', 'opens in a new window');
  });
})();
