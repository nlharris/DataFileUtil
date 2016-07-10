package DataFileUtil::DataFileUtilClient;

use JSON::RPC::Client;
use POSIX;
use strict;
use Data::Dumper;
use URI;
use Bio::KBase::Exceptions;
my $get_time = sub { time, 0 };
eval {
    require Time::HiRes;
    $get_time = sub { Time::HiRes::gettimeofday() };
};

use Bio::KBase::AuthToken;

# Client version should match Impl version
# This is a Semantic Version number,
# http://semver.org
our $VERSION = "0.1.0";

=head1 NAME

DataFileUtil::DataFileUtilClient

=head1 DESCRIPTION


Contains utilities for saving and retrieving data to and from KBase data
services. Requires Shock 0.9.6+ and Workspace Service 0.4.1+.


=cut

sub new
{
    my($class, $url, @args) = @_;
    

    my $self = {
	client => DataFileUtil::DataFileUtilClient::RpcClient->new,
	url => $url,
	headers => [],
    };

    chomp($self->{hostname} = `hostname`);
    $self->{hostname} ||= 'unknown-host';

    #
    # Set up for propagating KBRPC_TAG and KBRPC_METADATA environment variables through
    # to invoked services. If these values are not set, we create a new tag
    # and a metadata field with basic information about the invoking script.
    #
    if ($ENV{KBRPC_TAG})
    {
	$self->{kbrpc_tag} = $ENV{KBRPC_TAG};
    }
    else
    {
	my ($t, $us) = &$get_time();
	$us = sprintf("%06d", $us);
	my $ts = strftime("%Y-%m-%dT%H:%M:%S.${us}Z", gmtime $t);
	$self->{kbrpc_tag} = "C:$0:$self->{hostname}:$$:$ts";
    }
    push(@{$self->{headers}}, 'Kbrpc-Tag', $self->{kbrpc_tag});

    if ($ENV{KBRPC_METADATA})
    {
	$self->{kbrpc_metadata} = $ENV{KBRPC_METADATA};
	push(@{$self->{headers}}, 'Kbrpc-Metadata', $self->{kbrpc_metadata});
    }

    if ($ENV{KBRPC_ERROR_DEST})
    {
	$self->{kbrpc_error_dest} = $ENV{KBRPC_ERROR_DEST};
	push(@{$self->{headers}}, 'Kbrpc-Errordest', $self->{kbrpc_error_dest});
    }

    #
    # This module requires authentication.
    #
    # We create an auth token, passing through the arguments that we were (hopefully) given.

    {
	my $token = Bio::KBase::AuthToken->new(@args);
	
	if (!$token->error_message)
	{
	    $self->{token} = $token->token;
	    $self->{client}->{token} = $token->token;
	}
    }

    my $ua = $self->{client}->ua;	 
    my $timeout = $ENV{CDMI_TIMEOUT} || (30 * 60);	 
    $ua->timeout($timeout);
    bless $self, $class;
    #    $self->_validate_version();
    return $self;
}




=head2 shock_to_file

  $out = $obj->shock_to_file($params)

=over 4

=item Parameter and return types

=begin html

<pre>
$params is a DataFileUtil.ShockToFileParams
$out is a DataFileUtil.ShockToFileOutput
ShockToFileParams is a reference to a hash where the following keys are defined:
	shock_id has a value which is a string
	file_path has a value which is a string
	unpack has a value which is a DataFileUtil.boolean
boolean is an int
ShockToFileOutput is a reference to a hash where the following keys are defined:
	node_file_name has a value which is a string
	attributes has a value which is a reference to a hash where the key is a string and the value is an UnspecifiedObject, which can hold any non-null object

</pre>

=end html

=begin text

$params is a DataFileUtil.ShockToFileParams
$out is a DataFileUtil.ShockToFileOutput
ShockToFileParams is a reference to a hash where the following keys are defined:
	shock_id has a value which is a string
	file_path has a value which is a string
	unpack has a value which is a DataFileUtil.boolean
boolean is an int
ShockToFileOutput is a reference to a hash where the following keys are defined:
	node_file_name has a value which is a string
	attributes has a value which is a reference to a hash where the key is a string and the value is an UnspecifiedObject, which can hold any non-null object


=end text

=item Description

Download a file from Shock.

=back

=cut

 sub shock_to_file
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function shock_to_file (received $n, expecting 1)");
    }
    {
	my($params) = @args;

	my @_bad_arguments;
        (ref($params) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument 1 \"params\" (value was \"$params\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to shock_to_file:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'shock_to_file');
	}
    }

    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
	    method => "DataFileUtil.shock_to_file",
	    params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'shock_to_file',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method shock_to_file",
					    status_line => $self->{client}->status_line,
					    method_name => 'shock_to_file',
				       );
    }
}
 


=head2 file_to_shock

  $out = $obj->file_to_shock($params)

=over 4

=item Parameter and return types

=begin html

<pre>
$params is a DataFileUtil.FileToShockParams
$out is a DataFileUtil.FileToShockOutput
FileToShockParams is a reference to a hash where the following keys are defined:
	file_path has a value which is a string
	attributes has a value which is a reference to a hash where the key is a string and the value is an UnspecifiedObject, which can hold any non-null object
	make_handle has a value which is a DataFileUtil.boolean
	gzip has a value which is a DataFileUtil.boolean
boolean is an int
FileToShockOutput is a reference to a hash where the following keys are defined:
	shock_id has a value which is a string
	handle_id has a value which is a string

</pre>

=end html

=begin text

$params is a DataFileUtil.FileToShockParams
$out is a DataFileUtil.FileToShockOutput
FileToShockParams is a reference to a hash where the following keys are defined:
	file_path has a value which is a string
	attributes has a value which is a reference to a hash where the key is a string and the value is an UnspecifiedObject, which can hold any non-null object
	make_handle has a value which is a DataFileUtil.boolean
	gzip has a value which is a DataFileUtil.boolean
boolean is an int
FileToShockOutput is a reference to a hash where the following keys are defined:
	shock_id has a value which is a string
	handle_id has a value which is a string


=end text

=item Description

Load a file to Shock.

=back

=cut

 sub file_to_shock
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function file_to_shock (received $n, expecting 1)");
    }
    {
	my($params) = @args;

	my @_bad_arguments;
        (ref($params) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument 1 \"params\" (value was \"$params\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to file_to_shock:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'file_to_shock');
	}
    }

    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
	    method => "DataFileUtil.file_to_shock",
	    params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'file_to_shock',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method file_to_shock",
					    status_line => $self->{client}->status_line,
					    method_name => 'file_to_shock',
				       );
    }
}
 


=head2 copy_shock_node

  $out = $obj->copy_shock_node($params)

=over 4

=item Parameter and return types

=begin html

<pre>
$params is a DataFileUtil.CopyShockNodeParams
$out is a DataFileUtil.CopyShockNodeOutput
CopyShockNodeParams is a reference to a hash where the following keys are defined:
	shock_id has a value which is a string
CopyShockNodeOutput is a reference to a hash where the following keys are defined:
	shock_id has a value which is a string

</pre>

=end html

=begin text

$params is a DataFileUtil.CopyShockNodeParams
$out is a DataFileUtil.CopyShockNodeOutput
CopyShockNodeParams is a reference to a hash where the following keys are defined:
	shock_id has a value which is a string
CopyShockNodeOutput is a reference to a hash where the following keys are defined:
	shock_id has a value which is a string


=end text

=item Description

Copy a Shock node.

=back

=cut

 sub copy_shock_node
{
    my($self, @args) = @_;

# Authentication: required

    if ((my $n = @args) != 1)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function copy_shock_node (received $n, expecting 1)");
    }
    {
	my($params) = @args;

	my @_bad_arguments;
        (ref($params) eq 'HASH') or push(@_bad_arguments, "Invalid type for argument 1 \"params\" (value was \"$params\")");
        if (@_bad_arguments) {
	    my $msg = "Invalid arguments passed to copy_shock_node:\n" . join("", map { "\t$_\n" } @_bad_arguments);
	    Bio::KBase::Exceptions::ArgumentValidationError->throw(error => $msg,
								   method_name => 'copy_shock_node');
	}
    }

    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
	    method => "DataFileUtil.copy_shock_node",
	    params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'copy_shock_node',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method copy_shock_node",
					    status_line => $self->{client}->status_line,
					    method_name => 'copy_shock_node',
				       );
    }
}
 


=head2 versions

  $wsver, $shockver = $obj->versions()

=over 4

=item Parameter and return types

=begin html

<pre>
$wsver is a string
$shockver is a string

</pre>

=end html

=begin text

$wsver is a string
$shockver is a string


=end text

=item Description

Get the versions of the Workspace service and Shock service.

=back

=cut

 sub versions
{
    my($self, @args) = @_;

# Authentication: none

    if ((my $n = @args) != 0)
    {
	Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
							       "Invalid argument count for function versions (received $n, expecting 0)");
    }

    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
	    method => "DataFileUtil.versions",
	    params => \@args,
    });
    if ($result) {
	if ($result->is_error) {
	    Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
					       code => $result->content->{error}->{code},
					       method_name => 'versions',
					       data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
					      );
	} else {
	    return wantarray ? @{$result->result} : $result->result->[0];
	}
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method versions",
					    status_line => $self->{client}->status_line,
					    method_name => 'versions',
				       );
    }
}
 
  
sub status
{
    my($self, @args) = @_;
    if ((my $n = @args) != 0) {
        Bio::KBase::Exceptions::ArgumentValidationError->throw(error =>
                                   "Invalid argument count for function status (received $n, expecting 0)");
    }
    my $url = $self->{url};
    my $result = $self->{client}->call($url, $self->{headers}, {
        method => "DataFileUtil.status",
        params => \@args,
    });
    if ($result) {
        if ($result->is_error) {
            Bio::KBase::Exceptions::JSONRPC->throw(error => $result->error_message,
                           code => $result->content->{error}->{code},
                           method_name => 'status',
                           data => $result->content->{error}->{error} # JSON::RPC::ReturnObject only supports JSONRPC 1.1 or 1.O
                          );
        } else {
            return wantarray ? @{$result->result} : $result->result->[0];
        }
    } else {
        Bio::KBase::Exceptions::HTTP->throw(error => "Error invoking method status",
                        status_line => $self->{client}->status_line,
                        method_name => 'status',
                       );
    }
}
   

sub version {
    my ($self) = @_;
    my $result = $self->{client}->call($self->{url}, $self->{headers}, {
        method => "DataFileUtil.version",
        params => [],
    });
    if ($result) {
        if ($result->is_error) {
            Bio::KBase::Exceptions::JSONRPC->throw(
                error => $result->error_message,
                code => $result->content->{code},
                method_name => 'versions',
            );
        } else {
            return wantarray ? @{$result->result} : $result->result->[0];
        }
    } else {
        Bio::KBase::Exceptions::HTTP->throw(
            error => "Error invoking method versions",
            status_line => $self->{client}->status_line,
            method_name => 'versions',
        );
    }
}

sub _validate_version {
    my ($self) = @_;
    my $svr_version = $self->version();
    my $client_version = $VERSION;
    my ($cMajor, $cMinor) = split(/\./, $client_version);
    my ($sMajor, $sMinor) = split(/\./, $svr_version);
    if ($sMajor != $cMajor) {
        Bio::KBase::Exceptions::ClientServerIncompatible->throw(
            error => "Major version numbers differ.",
            server_version => $svr_version,
            client_version => $client_version
        );
    }
    if ($sMinor < $cMinor) {
        Bio::KBase::Exceptions::ClientServerIncompatible->throw(
            error => "Client minor version greater than Server minor version.",
            server_version => $svr_version,
            client_version => $client_version
        );
    }
    if ($sMinor > $cMinor) {
        warn "New client version available for DataFileUtil::DataFileUtilClient\n";
    }
    if ($sMajor == 0) {
        warn "DataFileUtil::DataFileUtilClient version is $svr_version. API subject to change.\n";
    }
}

=head1 TYPES



=head2 boolean

=over 4



=item Description

A boolean - 0 for false, 1 for true.
@range (0, 1)


=item Definition

=begin html

<pre>
an int
</pre>

=end html

=begin text

an int

=end text

=back



=head2 ShockToFileParams

=over 4



=item Description

Input for the shock_to_file function.

Required parameters:
shock_id - the ID of the Shock node.
file_path - the location to save the file output. If this is a
    directory, the file will be named as per the filename in Shock.

Optional parameters:
unpack - if the file is compressed and / or a file bundle, it will be
    decompressed and unbundled into the directory containing the
    original output file. unpack supports gzip, bzip2, tar, and zip
    files. Default false. Currently unsupported.


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
shock_id has a value which is a string
file_path has a value which is a string
unpack has a value which is a DataFileUtil.boolean

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
shock_id has a value which is a string
file_path has a value which is a string
unpack has a value which is a DataFileUtil.boolean


=end text

=back



=head2 ShockToFileOutput

=over 4



=item Description

Output from the shock_to_file function.

   node_file_name - the filename of the file stored in Shock.
   attributes - the file attributes, if any, stored in Shock.


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
node_file_name has a value which is a string
attributes has a value which is a reference to a hash where the key is a string and the value is an UnspecifiedObject, which can hold any non-null object

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
node_file_name has a value which is a string
attributes has a value which is a reference to a hash where the key is a string and the value is an UnspecifiedObject, which can hold any non-null object


=end text

=back



=head2 FileToShockParams

=over 4



=item Description

Input for the file_to_shock function.

Required parameters:
file_path - the location of the file to load to Shock.

Optional parameters:
attributes - user-specified attributes to save to the Shock node along
    with the file.
make_handle - make a Handle Service handle for the shock node. Default
    false.
gzip - gzip the file before loading it to Shock. This will create a
    file_path.gz file prior to upload. Default false.


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
file_path has a value which is a string
attributes has a value which is a reference to a hash where the key is a string and the value is an UnspecifiedObject, which can hold any non-null object
make_handle has a value which is a DataFileUtil.boolean
gzip has a value which is a DataFileUtil.boolean

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
file_path has a value which is a string
attributes has a value which is a reference to a hash where the key is a string and the value is an UnspecifiedObject, which can hold any non-null object
make_handle has a value which is a DataFileUtil.boolean
gzip has a value which is a DataFileUtil.boolean


=end text

=back



=head2 FileToShockOutput

=over 4



=item Description

Output of the file_to_shock function.

    shock_id - the ID of the new Shock node.
    handle_id - the handle ID for the new handle, if created. Null
       otherwise.


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
shock_id has a value which is a string
handle_id has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
shock_id has a value which is a string
handle_id has a value which is a string


=end text

=back



=head2 CopyShockNodeParams

=over 4



=item Description

Input for the copy_shock_node function.

       shock_id - the id of the node to copy.


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
shock_id has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
shock_id has a value which is a string


=end text

=back



=head2 CopyShockNodeOutput

=over 4



=item Description

Output of the copy_shock_node function.

 shock_id - the id of the new Shock node.


=item Definition

=begin html

<pre>
a reference to a hash where the following keys are defined:
shock_id has a value which is a string

</pre>

=end html

=begin text

a reference to a hash where the following keys are defined:
shock_id has a value which is a string


=end text

=back



=cut

package DataFileUtil::DataFileUtilClient::RpcClient;
use base 'JSON::RPC::Client';
use POSIX;
use strict;

#
# Override JSON::RPC::Client::call because it doesn't handle error returns properly.
#

sub call {
    my ($self, $uri, $headers, $obj) = @_;
    my $result;


    {
	if ($uri =~ /\?/) {
	    $result = $self->_get($uri);
	}
	else {
	    Carp::croak "not hashref." unless (ref $obj eq 'HASH');
	    $result = $self->_post($uri, $headers, $obj);
	}

    }

    my $service = $obj->{method} =~ /^system\./ if ( $obj );

    $self->status_line($result->status_line);

    if ($result->is_success) {

        return unless($result->content); # notification?

        if ($service) {
            return JSON::RPC::ServiceObject->new($result, $self->json);
        }

        return JSON::RPC::ReturnObject->new($result, $self->json);
    }
    elsif ($result->content_type eq 'application/json')
    {
        return JSON::RPC::ReturnObject->new($result, $self->json);
    }
    else {
        return;
    }
}


sub _post {
    my ($self, $uri, $headers, $obj) = @_;
    my $json = $self->json;

    $obj->{version} ||= $self->{version} || '1.1';

    if ($obj->{version} eq '1.0') {
        delete $obj->{version};
        if (exists $obj->{id}) {
            $self->id($obj->{id}) if ($obj->{id}); # if undef, it is notification.
        }
        else {
            $obj->{id} = $self->id || ($self->id('JSON::RPC::Client'));
        }
    }
    else {
        # $obj->{id} = $self->id if (defined $self->id);
	# Assign a random number to the id if one hasn't been set
	$obj->{id} = (defined $self->id) ? $self->id : substr(rand(),2);
    }

    my $content = $json->encode($obj);

    $self->ua->post(
        $uri,
        Content_Type   => $self->{content_type},
        Content        => $content,
        Accept         => 'application/json',
	@$headers,
	($self->{token} ? (Authorization => $self->{token}) : ()),
    );
}



1;
