(function () {
  var welcome = document.getElementById('welcome');
  var wizard = document.getElementById('wizard');
  var tagline = document.getElementById('tagline');
  var container = document.getElementById('onbContainer');
  if (!welcome || !wizard) return;

  // Selection Grid Handlers
  function handleSelectionClick(item, maxSelections = 1) {
    const input = item.closest('.panel').querySelector('input[type="hidden"]');
    const grid = item.closest('.selection-grid');
    const selectedItems = grid.querySelectorAll('.selection-item.selected');
    
    if (item.classList.contains('disabled')) return;
    
    if (item.classList.contains('selected')) {
      // Deselect
      item.classList.remove('selected');
      if (maxSelections === 1) {
        input.value = '';
      } else {
        // For multiple selections, maintain array in hidden input
        const currentValues = input.value ? input.value.split(',') : [];
        const newValues = currentValues.filter(v => v !== item.dataset.value);
        input.value = newValues.join(',');
      }
      // Enable other items if we were at max
      if (selectedItems.length === maxSelections) {
        grid.querySelectorAll('.selection-item.disabled').forEach(i => {
          if (!i.classList.contains('selected')) i.classList.remove('disabled');
        });
      }
    } else {
      // Select
      if (maxSelections === 1) {
        // Single selection - deselect others
        selectedItems.forEach(selected => selected.classList.remove('selected'));
        item.classList.add('selected');
        input.value = item.dataset.value;
      } else {
        // Multiple selection
        if (selectedItems.length < maxSelections) {
          item.classList.add('selected');
          const currentValues = input.value ? input.value.split(',') : [];
          currentValues.push(item.dataset.value);
          input.value = currentValues.join(',');
          
          // If we've hit max selections, disable unselected items
          if (currentValues.length === maxSelections) {
            grid.querySelectorAll('.selection-item:not(.selected)').forEach(i => {
              i.classList.add('disabled');
            });
          }
        }
      }
    }
  }

  // Initialize selection grids
  document.querySelectorAll('.selection-grid').forEach(grid => {
    const maxSelections = parseInt(grid.dataset.maxSelections || '1', 10);
    grid.querySelectorAll('.selection-item').forEach(item => {
      item.addEventListener('click', () => handleSelectionClick(item, maxSelections));
    });
  });

  // After welcome fades, show tagline then wizard
  setTimeout(function () {
    if (tagline) tagline.classList.remove('d-none');
  }, 2500);
  setTimeout(function () {
    if (tagline) tagline.classList.add('d-none');
    if (container) container.classList.remove('d-none');
    wizard.classList.remove('d-none');
  }, 4200);

  var current = 1;
  var total = 6;
  var prevBtn = document.getElementById('prevBtn');
  var nextBtn = document.getElementById('nextBtn');
  var form = document.getElementById('onbForm');
  var onbVideo = document.getElementById('onbVideo');

  function showStep(step) {
    for (var i = 1; i <= total; i++) {
      var p = form.querySelector('.panel[data-step="' + i + '"]');
      if (p) p.classList.toggle('d-none', i !== step);
      var d = document.querySelector('.progress-dots .dot[data-step="' + i + '"]');
      if (d) d.classList.toggle('active', i <= step);
    }
    // Swap video per step if dataset provided
    if (onbVideo) {
      var key = 'step' + step;
      var nextSrc = onbVideo.dataset[key];
      if (nextSrc) onbVideo.src = nextSrc;
    }
    prevBtn.disabled = (step === 1);
    nextBtn.textContent = (step === total) ? 'Finish' : 'Next';
  }

  prevBtn.addEventListener('click', function () {
    if (current > 1) {
      current -= 1;
      showStep(current);
    }
  });

  nextBtn.addEventListener('click', function () {
    // Validate current step
    var panel = form.querySelector('.panel[data-step="' + current + '"]');
    if (panel) {
      var input = panel.querySelector('input[type="hidden"], input:not([type="hidden"]), select');
      if (input && input.required && !input.value) {
        alert('Please make a selection before proceeding.');
        return;
      }
      // Additional validation for interests (minimum selection)
      if (input && input.name === 'interests' && input.required) {
        const selectedCount = input.value.split(',').filter(v => v).length;
        if (selectedCount < 1) {
          alert('Please select at least one interest.');
          return;
        }
      }
    }
    if (current < total) {
      current += 1;
      showStep(current);
    } else {
      // Collect and submit preferences
      var payload = {
        age: form.querySelector('input[name="age"]').value,
        country: form.querySelector('input[name="country"]').value,
        interests: form.querySelector('input[name="interests"]').value,
        native_language: form.querySelector('input[name="native_language"]').value,
        target_language: form.querySelector('input[name="target_language"]').value,
        level: form.querySelector('input[name="level"]').value,
      };
      fetch('/onboarding', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      }).then(function (r) { return r.json(); }).then(function (res) {
        if (res && res.ok) {
          // Show thank-you interstitial like the tagline
          if (container) container.classList.add('d-none');
          if (wizard) wizard.classList.add('d-none');
          var endTag = document.createElement('div');
          endTag.className = 'tagline';
          endTag.textContent = 'Thank you for answering the questions, enjoy your learning~';
          document.body.appendChild(endTag);
          setTimeout(function(){ window.location.href = '/dashboard'; }, 2000);
        } else {
          alert('Failed to save preferences.');
        }
      }).catch(function () { alert('Failed to save preferences.'); });
    }
  });

  // Start on step 1
  showStep(1);
})();


