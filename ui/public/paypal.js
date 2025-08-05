(async() => {
  PayPal.Donation.Button({
    env: 'production',
    hosted_button_id: 'AENZ9E63F85G8',
    image: {
      src: 'https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif',
      alt: 'Donate with PayPal button',
      title: 'PayPal - The safer, easier way to pay online!',
    }
  }).render('#donate-button');
})();
