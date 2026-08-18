(function () {
  'use strict';

  const activities = [
    'Prince from Nigeria just started a live stream',
    'Ken from Ireland just paid for the Starter plan',
    'Amara from Lagos just uploaded a new Look',
    'Fatima from Abuja just went live with AI transformation',
    'James from London just joined Creoveya',
    'Chidi from Enugu just purchased the Creator plan',
    'Sophie from Toronto just started streaming',
    'Emeka from Port Harcourt just switched his look',
    'Liam from Dublin just went live',
    'Ngozi from Owerri just topped up her credits',
    'Carlos from Madrid just created an account',
    'Blessing from Kano just started a live session',
    'Ahmed from Cairo just paid via cryptocurrency',
    'Grace from Ibadan just uploaded a reference photo',
    'David from Manchester just went live on Creoveya',
    'Chioma from Lagos just got approved for the Starter plan',
    'Yusuf from Kaduna just began streaming',
    'Olivia from Sydney just joined the platform',
    'Tunde from Lagos just paid for the Creator plan',
    'Mei from Singapore just started a live broadcast',
    'Ifeoma from Aba just switched to a new AI look',
    'Marco from Rome just signed up',
    'Aisha from Abuja just went live',
    'Kwame from Accra just purchased credits',
    'Ella from New York just joined Creoveya',
    'Segun from Ibadan just started streaming with AI',
    'Priya from Mumbai just topped up her account',
    'Emmanuel from Benin City just went live',
    'Hannah from Cape Town just registered',
    'Musa from Sokoto just paid via bank transfer',
    'Zainab from Kano just uploaded a new look',
    'Daniel from Berlin just began a live session',
    'Chinwe from Onitsha just bought the Starter plan',
    'Oliver from Auckland just joined the platform',
    'Bassey from Calabar just went live',
    'Ana from São Paulo just started streaming',
    'Ibrahim from Jos just switched his AI character',
    'Grace from Uyo just paid for credits',
    'Noah from Los Angeles just signed up',
    'Halima from Maiduguri just went live',
    'Femi from Lagos just topped up his account',
    'Charlotte from Melbourne just joined Creoveya',
    'Chukwuemeka from Owerri just started a live stream',
    'Amina from Abuja just uploaded a look',
    'Ethan from Chicago just paid via crypto',
    'Ruth from Warri just switched her look mid-stream',
    'Tobi from Lagos just began a live session',
    'Isabella from Dubai just registered',
    'Godwin from Benin City just purchased the Creator plan',
    'Mary from Enugu just went live on Creoveya',
    'Samuel from Ilorin just topped up his credits',
  ];

  let index = 0;
  let container = null;

  function createContainer() {
    container = document.createElement('div');
    container.id = 'activityToastContainer';
    container.style.cssText = 'position:fixed; bottom:20px; left:20px; z-index:1080; max-width:320px;';
    document.body.appendChild(container);
  }

  function showNext() {
    if (!container) createContainer();

    const text = activities[index % activities.length];
    index += 1;

    // ensure live-dot styles are added once
    if (!document.getElementById('activityToastStyles')) {
      const style = document.createElement('style');
      style.id = 'activityToastStyles';
      style.innerHTML = `
        #activityToastContainer .live-dot {
          width:10px;
          height:10px;
          border-radius:50%;
          background:#16a34a;
          box-shadow:0 0 8px rgba(22,163,74,0.6);
          animation:livePulse 1.6s infinite ease-in-out;
          flex-shrink:0;
        }
        @keyframes livePulse {
          0% { transform:scale(1); box-shadow:0 0 0 0 rgba(22,163,74,0.7); }
          50% { transform:scale(1.15); box-shadow:0 0 18px 8px rgba(22,163,74,0); }
          100% { transform:scale(1); box-shadow:0 0 0 0 rgba(22,163,74,0); }
        }
      `;
      document.head.appendChild(style);
    }

    const toast = document.createElement('div');
    toast.className = 'glass-card';
    toast.style.cssText = 'background:#fff; color:#000; padding:.75rem 1rem; margin-top:.5rem; display:flex; align-items:center; gap:.6rem; opacity:0; transform:translateY(10px); transition:opacity .35s ease, transform .35s ease; font-size:.82rem; border-radius:8px; box-shadow:0 6px 18px rgba(0,0,0,0.12);';
    toast.innerHTML = `
      <span class="live-dot" aria-hidden="true"></span>
      <span style="color:#000; font-weight:600;">${text}</span>
    `;
    container.appendChild(toast);

    requestAnimationFrame(() => {
      toast.style.opacity = '1';
      toast.style.transform = 'translateY(0)';
    });

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 400);
    }, 5000);

    const nextDelay = 6000 + Math.random() * 5000; // 6-11s between notifications
    setTimeout(showNext, nextDelay);
  }

  document.addEventListener('DOMContentLoaded', () => {
    setTimeout(showNext, 3000); // first one appears 3s after page load
  });
})();
