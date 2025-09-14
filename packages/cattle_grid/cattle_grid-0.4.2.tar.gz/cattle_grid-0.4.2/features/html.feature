Feature: Interacting with Activity Pub objects as HTML

    Background:
        Given A new user called "Alice"
        And "Alice" is in the "html_display" group
        And A new user called "Bob"
        And "Bob" follows "Alice"
        
    Scenario: Messages have url property
        When "Alice" publishes a message "Who stole my milk?" to her followers
        Then "Bob" receives a message saying "Who stole my milk?"
        And The received message contains an URL of mediatype "text/html"
        And The URL resolves to a webpage containing "Who stole my milk?"