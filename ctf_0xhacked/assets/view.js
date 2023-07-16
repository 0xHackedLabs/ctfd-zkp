CTFd._internal.challenge.data = undefined;

// TODO: Remove in CTFd v4.0
CTFd._internal.challenge.renderer = null;

CTFd._internal.challenge.preRender = function() {};

// TODO: Remove in CTFd v4.0
CTFd._internal.challenge.render = null;

CTFd._internal.challenge.postRender = function() {};


CTFd.pages.challenge.submitChallenge = async function(challengeId, challengeValue, preview = false) {
  if (CTFd._functions.challenge.submitChallenge) {
    CTFd._functions.challenge.submitChallenge(challengeId, challengeValue);
    return;
  }

  var fileInput = document.getElementById('zk_proof');
  var file = fileInput.files[0];

  var formData = new FormData();
  formData.append('file', file);
  formData.append("nonce", CTFd.config.csrfNonce);

  var upload_response = await fetch("/proof", {
    method: "POST",
    body: formData,
    credentials: "same-origin",
    headers: {
      "Accept": "application/json"
    }
  })
  var upload_result = await upload_response.json()

  challengeValue = upload_result.data.location;

  let url = `/api/v1/challenges/attempt`;
  if (preview === true || CTFd.config.preview === true) {
    url += "?preview=true";
  }

  const response = await CTFd.fetch(url, {
    method: "POST",
    body: JSON.stringify({
      challenge_id: challengeId,
      submission: challengeValue,
    }),
  });
  const result = await response.json();

  if (CTFd._functions.challenge.displaySubmissionResponse) {
    CTFd._functions.challenge.displaySubmissionResponse(result);
  }

  return result;
}
