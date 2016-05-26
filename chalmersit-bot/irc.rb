require 'rubygems'
require 'sinatra'
require 'json'

# IRC Config
IRC_HOST = 'deathstar.chalmers.it'
IRC_PORT = 6667
IRC_CHANNEL = '#digit'
IRC_NICK = 'Chalmersit-bot'
IRC_REALNAME = 'Chalmersit-bot'

post '/commit' do

  Thread.new do
    socket = TCPSocket.open(IRC_HOST, IRC_PORT)
    socket.puts("NICK #{IRC_NICK} \n")
    socket.puts("USER #{IRC_NICK} 8 * : #{IRC_REALNAME} \n")

    # Check if we have gotten write permission
    while line = socket.gets
      puts line
      if line.include? "#{IRC_NICK} +xw"
        break
      end
    end
    json = JSON.parse(request.env["rack.input"].read)
    #write to channel
    socket.puts("PRIVMSG #{IRC_CHANNEL} :#{json['message']} \n")
    #sleep so we don't close socket while sending msg
    sleep 2
    p socket.gets
    socket.close

    Thread.stop
  end

end
